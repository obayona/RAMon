#!/usr/bin/env python3
"""RAMon Chatbot Automated Test Runner

Reads test cases from test_cases.csv, runs each through the chatbot,
and uses an LLM judge to evaluate the responses. Results are stored
in test_results.csv.

Usage:
    python test_chatbot.py

Requires:
    - Install chatbot package: pip install -e ../chatbot
    - .env file with required environment variables
    - test_cases.csv in the same directory
"""
import asyncio
import csv
import json
import logging
import os
import sys
import uuid
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

load_dotenv()

logging.disable(logging.WARNING)

import structlog
structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.CRITICAL))

from chatbot import ChatbotBuilder, Product
from chatbot.adapters import PostgresProductRepository

_PRODUCT_COLUMNS = (
    "id, product_id, sku, name, description, categories, price, stock, in_stock, "
    "url, image_url, status"
)


class PostgresProductCatalog:
    """Look up a single product by product_id (text slug)."""

    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    async def get_product(self, product_id: str) -> Optional[Product]:
        async with self._pool.connection() as conn:
            cursor = await conn.execute(
                f"SELECT {_PRODUCT_COLUMNS} FROM products WHERE product_id = %s",
                (product_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return Product(
                id=row["id"],
                product_id=str(row["product_id"]),
                sku=row["sku"] or "",
                name=row["name"],
                description=row["description"] or "",
                categories=row["categories"] or "",
                price=row["price"],
                stock=row["stock"],
                in_stock=row["in_stock"] if row["in_stock"] is not None else True,
                url=row["url"] or "",
                image_url=row["image_url"] or "",
                status=row["status"] or "publish",
                similarity=None,
            )


def _get_database_url() -> str:
    return (
        f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
        f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
    )


@dataclass
class TestCase:
    test_id: str
    category: str
    conditions: str
    user_query: str
    expected_behavior: str
    expected_format: str
    success_criteria: str


@dataclass
class TestResult:
    test_id: str
    category: str
    user_query: str
    conditions: str
    expected_behavior: str
    expected_format: str
    success_criteria: str
    chatbot_response: str = ""
    tool_calls_log: str = ""
    recommendations_log: str = ""
    judge_verdict: str = ""
    passed: str = ""


def _normalize_curly_quotes(text: str) -> str:
    """Replace Unicode curly quotes with standard ASCII double quotes."""
    return text.replace("\u201c", '"').replace("\u201d", '"')


def load_test_cases(path: str) -> list[TestCase]:
    cases = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cond = row.get("Conditions", "").strip()
            if not cond or cond == "None":
                cond = ""
            else:
                cond = _normalize_curly_quotes(cond)
            cases.append(TestCase(
                test_id=row["Test_ID"].strip(),
                category=row["Category / Intent"].strip(),
                conditions=cond,
                user_query=row["User_Query"].strip(),
                expected_behavior=row["Expected_Behavior"].strip(),
                expected_format=row["Expected_Format"].strip(),
                success_criteria=row["Success_Criteria (Rubric for LLM Judge)"].strip(),
            ))
    return cases


def buffer_chatbot_response(result: dict) -> tuple[str, str, str]:
    """Extract and buffer all chatbot output into readable strings.

    Returns:
        (ai_response_text, tool_calls_log, recommendations_log)
    """
    messages = result.get("messages", [])
    recommendations = result.get("recommendations", [])

    ai_parts: list[str] = []
    tool_parts: list[str] = []

    for msg in messages:
        role = type(msg).__name__
        if role == "AIMessage":
            if getattr(msg, "tool_calls", None):
                for tc in msg.tool_calls:
                    tool_parts.append(
                        f"[ToolCall] {tc.get('name', '?')}({tc.get('args', {})})"
                    )
            content = getattr(msg, "content", "")
            if content:
                ai_parts.append(content)
        elif role == "ToolMessage":
            content = getattr(msg, "content", "")
            tool_parts.append(f"[ToolResult] {content}")

    ai_text = "\n".join(ai_parts)
    tool_log = "\n".join(tool_parts)

    rec_lines: list[str] = []
    for i, p in enumerate(recommendations, 1):
        name = p.get("name", "N/A") if isinstance(p, dict) else getattr(p, "name", "N/A")
        price = p.get("price", 0) if isinstance(p, dict) else getattr(p, "price", 0)
        desc = p.get("description", "") if isinstance(p, dict) else getattr(p, "description", "")
        rec_lines.append(f"{i}. {name} - ${price:.2f} | {desc[:100]}")
    rec_log = "\n".join(rec_lines)

    return ai_text, tool_log, rec_log


def judge_response(
    client: OpenAI,
    model: str,
    user_query: str,
    chatbot_response: str,
    recommendations: str,
    tool_calls: str,
    expected_behavior: str,
    expected_format: str,
    success_criteria: str,
) -> tuple[str, bool]:
    """Use LLM-as-judge to evaluate the chatbot response.

    Returns:
        (verdict_text, passed_bool)
    """
    full_response = chatbot_response
    if recommendations:
        full_response += f"\n\n[Product Recommendations]\n{recommendations}"
    if tool_calls:
        full_response += f"\n\n[Tool Calls]\n{tool_calls}"

    prompt = f"""You are an expert judge evaluating a chatbot's response for a computer hardware e-commerce store.

## User Query
{user_query}

## Chatbot Response
{full_response}

## Expected Behavior
{expected_behavior}

## Expected Format
{expected_format}

## Success Criteria (Rubric)
{success_criteria}

---
Evaluate the chatbot response against the expected behavior, format, and success criteria.
Provide a clear PASS or FAIL verdict on the first line, followed by a brief justification.

Format your response as:
VERDICT: PASS or FAIL
JUSTIFICATION: <your reasoning>"""

    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    verdict_text = completion.choices[0].message.content or ""
    passed = "VERDICT: PASS" in verdict_text.upper()
    return verdict_text, passed


async def run_tests():
    print("Loading test cases...", flush=True)
    test_cases = load_test_cases(os.path.join(os.path.dirname(__file__), "test_cases.csv"))
    print(f"Found {len(test_cases)} test cases.\n", flush=True)

    print("Initializing database pool...", flush=True)
    db_pool = AsyncConnectionPool(
        conninfo=_get_database_url(),
        min_size=2,
        max_size=10,
        open=False,
        kwargs={"autocommit": True, "row_factory": dict_row},
    )
    await db_pool.open()

    product_catalog = PostgresProductCatalog(db_pool)

    try:
        print("Building chatbot...", flush=True)
        bot = (
            ChatbotBuilder()
            .with_openai(
                api_key=os.environ.get("OPENAI_API_KEY"),
                model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=float(os.environ.get("OPENAI_TEMPERATURE", "0.0")),
            )
            .with_tavily(api_key=os.environ.get("TAVILY_API_KEY"))
            .with_product_repository(PostgresProductRepository(db_pool))
            .build()
        )
        print("Chatbot ready!\n", flush=True)

        judge_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        judge_model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

        results: list[TestResult] = []

        for tc in test_cases:
            print(f"--- {tc.test_id}: {tc.user_query[:60]}...", flush=True)

            current_product = None
            if tc.conditions:
                try:
                    cond = json.loads(tc.conditions)
                    pid = cond.get("current_product_id")
                    if pid:
                        current_product = await product_catalog.get_product(str(pid))
                        if current_product:
                            print(f"  Loaded product: {current_product['name']}", flush=True)
                        else:
                            print(f"  WARNING: product_id={pid} not found in DB", flush=True)
                except json.JSONDecodeError:
                    pass

            chat_id = f"test-{tc.test_id}-{uuid.uuid4().hex[:6]}"
            result = await bot.ainvoke(
                tc.user_query,
                current_product=current_product,
                chat_id=chat_id,
            )

            ai_text, tool_log, rec_log = buffer_chatbot_response(result)

            print(f"  AI response ({len(ai_text)} chars)", flush=True)

            verdict, passed = judge_response(
                client=judge_client,
                model=judge_model,
                user_query=tc.user_query,
                chatbot_response=ai_text,
                recommendations=rec_log,
                tool_calls=tool_log,
                expected_behavior=tc.expected_behavior,
                expected_format=tc.expected_format,
                success_criteria=tc.success_criteria,
            )
            status = "PASS" if passed else "FAIL"
            print(f"  Judge: {status}\n", flush=True)

            results.append(TestResult(
                test_id=tc.test_id,
                category=tc.category,
                user_query=tc.user_query,
                conditions=tc.conditions,
                expected_behavior=tc.expected_behavior,
                expected_format=tc.expected_format,
                success_criteria=tc.success_criteria,
                chatbot_response=ai_text,
                tool_calls_log=tool_log,
                recommendations_log=rec_log,
                judge_verdict=verdict,
                passed=status,
            ))

        output_path = os.path.join(os.path.dirname(__file__), "test_results.csv")
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Test_ID", "Category", "User_Query", "Conditions",
                "Expected_Behavior", "Expected_Format", "Success_Criteria",
                "Chatbot_Response", "Tool_Calls", "Recommendations",
                "Judge_Verdict", "Passed",
            ])
            for r in results:
                writer.writerow([
                    r.test_id, r.category, r.user_query, r.conditions,
                    r.expected_behavior, r.expected_format, r.success_criteria,
                    r.chatbot_response, r.tool_calls_log, r.recommendations_log,
                    r.judge_verdict, r.passed,
                ])

        total = len(results)
        passed_count = sum(1 for r in results if r.passed == "PASS")
        print(f"\n{'='*60}", flush=True)
        print(f"RESULTS: {passed_count}/{total} passed", flush=True)
        print(f"Output saved to: {output_path}", flush=True)
        print(f"{'='*60}", flush=True)

    finally:
        await db_pool.close()


if __name__ == "__main__":
    asyncio.run(run_tests())
