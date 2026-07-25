<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Admin;

use Ramon\Chatbot\Ports\OptionStore;
use Ramon\Chatbot\Services\JwtService;

/**
 * Admin chats page for RAMon Chatbot.
 *
 * Two-column responsive layout: chat list on the left, selected chat on
 * the right.  Individual chats are loaded asynchronously via the backend
 * REST API.  The URL hash is updated so a page reload re-opens the last
 * viewed chat.
 */
final class ChatsPage
{
    public function __construct(
        private readonly OptionStore $options,
        private readonly JwtService $jwt,
    ) {
    }

    /**
     * Render the chats page.
     */
    public function renderPage(): void
    {
        $apiUrl = (string) $this->options->get('ramon_api_url', '');
        $token = $this->jwt->generate();

        ?>
        <style>
            .ramon-chats-layout {
                display: flex;
                gap: 1rem;
                margin-top: 1rem;
                min-height: 75vh;
                position: relative;
            }
            .ramon-chats-list {
                width: 320px;
                min-width: 320px;
                background: #fff;
                border: 1px solid #c3c4c7;
                border-radius: 4px;
                overflow-y: auto;
                max-height: 80vh;
            }
            .ramon-chats-list .ramon-list-header {
                padding: 0.75rem 1rem;
                border-bottom: 1px solid #e2e8f0;
                font-weight: 600;
                color: #1e293b;
                font-size: 14px;
            }
            .ramon-chats-list .ramon-list-empty {
                padding: 2rem 1rem;
                text-align: center;
                color: #64748b;
            }
            .ramon-chats-list .ramon-list-loading {
                padding: 2rem 1rem;
                text-align: center;
                color: #94a3b8;
            }
            .ramon-chat-item {
                padding: 0.75rem 1rem;
                border-bottom: 1px solid #f1f5f9;
                cursor: pointer;
                transition: background 0.15s;
            }
            .ramon-chat-item:hover {
                background: #f8fafc;
            }
            .ramon-chat-item.ramon-chat-active {
                background: #eff6ff;
                border-left: 3px solid #3b82f6;
            }
            .ramon-chat-item-title {
                font-size: 13px;
                font-weight: 600;
                color: #1e293b;
                margin-bottom: 2px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            .ramon-chat-item-date {
                font-size: 12px;
                color: #94a3b8;
            }
            .ramon-chat-detail {
                flex: 1;
                background: #fff;
                border: 1px solid #c3c4c7;
                border-radius: 4px;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            .ramon-chat-detail-empty {
                flex: 1;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #94a3b8;
                font-size: 14px;
            }
            .ramon-chat-detail-header {
                padding: 0.75rem 1rem;
                border-bottom: 1px solid #e2e8f0;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            .ramon-chat-back-btn {
                display: none;
                background: none;
                border: none;
                cursor: pointer;
                font-size: 18px;
                color: #3b82f6;
                padding: 0 0.25rem;
                line-height: 1;
            }
            .ramon-chat-detail-header-title {
                font-weight: 600;
                color: #1e293b;
                font-size: 14px;
            }
            .ramon-chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 1rem;
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
            }
            .ramon-msg {
                max-width: 80%;
                padding: 0.5rem 0.85rem;
                border-radius: 14px;
                line-height: 1.4;
                font-size: 14px;
                word-wrap: break-word;
            }
            .ramon-msg-human {
                align-self: flex-end;
                background: #3b82f6;
                color: #fff;
                border-bottom-right-radius: 4px;
            }
            .ramon-msg-ai {
                align-self: flex-start;
                background: #f1f5f9;
                color: #1e293b;
                border-bottom-left-radius: 4px;
            }
            .ramon-msg-products {
                align-self: flex-start;
                width: 100%;
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
                margin-top: 0.25rem;
            }
            .ramon-product-card {
                background: #fff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 0.6rem;
                flex: 1 1 160px;
            }
            .ramon-product-card img {
                width: 100%;
                height: 120px;
                object-fit: contain;
                border-radius: 4px;
                margin-bottom: 0.4rem;
                background: #f8fafc;
            }
            .ramon-product-card h4 {
                font-size: 13px;
                color: #1e293b;
                margin: 0 0 0.2rem;
            }
            .ramon-product-card p {
                font-size: 12px;
                color: #64748b;
                margin: 0;
            }
            .ramon-product-card .ramon-price {
                font-weight: 600;
                color: #059669;
                margin-top: 0.3rem;
                font-size: 13px;
            }
            @media (max-width: 782px) {
                .ramon-chats-layout {
                    flex-direction: column;
                    min-height: auto;
                }
                .ramon-chats-list {
                    width: 100%;
                    min-width: 0;
                    max-height: none;
                }
                .ramon-chat-detail {
                    position: fixed;
                    top: 32px;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    z-index: 99999;
                    border-radius: 0;
                    border: none;
                    display: none;
                    flex-direction: column;
                }
                .ramon-chats-layout.ramon-chat-open .ramon-chat-detail {
                    display: flex;
                }
                .ramon-chats-layout.ramon-chat-open .ramon-chats-list {
                    display: none;
                }
                .ramon-chat-back-btn {
                    display: inline-block;
                }
            }
        </style>

        <div class="wrap">
            <h1>RAMon Chatbot — Chats</h1>

            <div id="ramon-chats-layout" class="ramon-chats-layout">
                <div class="ramon-chats-list">
                    <div class="ramon-list-header">Conversations</div>
                    <div id="ramon-list-body" class="ramon-list-loading">Loading chats…</div>
                </div>

                <div class="ramon-chat-detail">
                    <div id="ramon-detail-empty" class="ramon-chat-detail-empty">
                        Select a conversation to view it.
                    </div>
                    <div id="ramon-detail-content" style="display:none;flex-direction:column;height:100%;">
                        <div class="ramon-chat-detail-header">
                            <button class="ramon-chat-back-btn" id="ramon-back-btn" title="Back to list">&#8592;</button>
                            <span class="ramon-chat-detail-header-title" id="ramon-detail-title"></span>
                        </div>
                        <div class="ramon-chat-messages" id="ramon-chat-messages"></div>
                    </div>
                </div>
            </div>
        </div>

        <script id="ramon-chats-config" type="application/json"><?php
            echo \wp_json_encode(['apiUrl' => $apiUrl, 'token' => $token]);
        ?></script>

        <script>
        (function () {
            const cfg = JSON.parse(document.getElementById('ramon-chats-config').textContent);
            const apiUrl = cfg.apiUrl;
            const token = cfg.token;
            const layout = document.getElementById('ramon-chats-layout');
            const listBody = document.getElementById('ramon-list-body');
            const detailEmpty = document.getElementById('ramon-detail-empty');
            const detailContent = document.getElementById('ramon-detail-content');
            const detailTitle = document.getElementById('ramon-detail-title');
            const chatMessages = document.getElementById('ramon-chat-messages');
            const backBtn = document.getElementById('ramon-back-btn');
            let activeChatId = null;

            // ── Helpers ────────────────────────────────────────────

            function headers() { return { 'Authorization': 'Bearer ' + token }; }

            function esc(s) {
                var d = document.createElement('div');
                d.textContent = s;
                return d.innerHTML;
            }

            function formatDate(iso) {
                if (!iso) return '';
                try {
                    return new Date(iso).toLocaleString();
                } catch (e) {
                    return iso;
                }
            }

            function shortId(id) {
                return id.length > 24 ? id.slice(0, 24) + '…' : id;
            }

            // ── URL hash ───────────────────────────────────────────

            function getHashChatId() {
                var m = location.hash.match(/chat_id=([^&]+)/);
                return m ? decodeURIComponent(m[1]) : null;
            }

            function setHashChatId(id) {
                if (id) {
                    location.hash = 'chat_id=' + encodeURIComponent(id);
                } else {
                    history.pushState('', '', location.pathname + location.search);
                }
            }

            // ── Chat list ──────────────────────────────────────────

            async function loadChats() {
                if (!apiUrl || !token) {
                    listBody.className = '';
                    listBody.innerHTML = '<div class="ramon-list-empty">Configure the API URL and App Key on the Settings page.</div>';
                    return;
                }

                try {
                    var resp = await fetch(apiUrl + '/chats', { headers: headers() });
                    if (!resp.ok) throw new Error(resp.status);
                    var chats = await resp.json();
                } catch (e) {
                    listBody.className = '';
                    listBody.innerHTML = '<div class="ramon-list-empty">Failed to load chats.</div>';
                    return;
                }

                if (!chats.length) {
                    listBody.className = '';
                    listBody.innerHTML = '<div class="ramon-list-empty">No conversations found.</div>';
                    return;
                }

                listBody.className = '';
                listBody.innerHTML = '';

                chats.forEach(function (chat) {
                    var item = document.createElement('div');
                    item.className = 'ramon-chat-item';
                    item.dataset.chatId = chat.thread_id;
                    item.innerHTML = '<div class="ramon-chat-item-title">' + esc(shortId(chat.thread_id)) + '</div>'
                        + '<div class="ramon-chat-item-date">' + esc(formatDate(chat.created_at)) + '</div>';
                    item.addEventListener('click', function () { selectChat(chat.thread_id); });
                    listBody.appendChild(item);
                });

                var hashId = getHashChatId();
                if (hashId) selectChat(hashId);
            }

            // ── Chat detail ────────────────────────────────────────

            async function selectChat(chatId) {
                activeChatId = chatId;
                setHashChatId(chatId);

                // Highlight in list
                listBody.querySelectorAll('.ramon-chat-item').forEach(function (el) {
                    el.classList.toggle('ramon-chat-active', el.dataset.chatId === chatId);
                });

                detailEmpty.style.display = 'none';
                detailContent.style.display = 'flex';
                detailTitle.textContent = shortId(chatId);
                chatMessages.innerHTML = '';
                layout.classList.add('ramon-chat-open');

                // Show a loading state
                var loading = document.createElement('div');
                loading.className = 'ramon-msg ramon-msg-ai';
                loading.textContent = 'Loading…';
                chatMessages.appendChild(loading);

                try {
                    var resp = await fetch(apiUrl + '/chat/' + encodeURIComponent(chatId), { headers: headers() });
                    if (!resp.ok) throw new Error(resp.status);
                    var messages = await resp.json();
                } catch (e) {
                    chatMessages.innerHTML = '';
                    var err = document.createElement('div');
                    err.className = 'ramon-msg ramon-msg-ai';
                    err.textContent = 'Failed to load conversation.';
                    chatMessages.appendChild(err);
                    return;
                }

                chatMessages.innerHTML = '';
                messages.forEach(function (msg) {
                    appendMsg(msg.content, msg.role === 'user' ? 'human' : 'ai');
                    if (msg.products && msg.products.length) {
                        renderProducts(msg.products);
                    }
                });
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

            function deselectChat() {
                activeChatId = null;
                setHashChatId(null);
                layout.classList.remove('ramon-chat-open');
                detailEmpty.style.display = 'flex';
                detailContent.style.display = 'none';
                listBody.querySelectorAll('.ramon-chat-item').forEach(function (el) {
                    el.classList.remove('ramon-chat-active');
                });
            }

            // ── Rendering ──────────────────────────────────────────

            function appendMsg(text, cls) {
                var el = document.createElement('div');
                el.className = 'ramon-msg ramon-msg-' + cls;
                el.textContent = text;
                chatMessages.appendChild(el);
            }

            function renderProducts(products) {
                if (!products || !products.length) return;
                var container = document.createElement('div');
                container.className = 'ramon-msg-products';
                products.forEach(function (p) {
                    var card = document.createElement('div');
                    card.className = 'ramon-product-card';
                    var img = p.image_url ? '<img src="' + esc(p.image_url) + '" alt="' + esc(p.name) + '" loading="lazy" />' : '';
                    card.innerHTML = img
                        + '<h4>' + esc(p.name) + '</h4>'
                        + '<p>' + esc((p.description || '').slice(0, 100)) + '</p>'
                        + '<div class="ramon-price">$' + (p.price || 0).toFixed(2) + '</div>';
                    container.appendChild(card);
                });
                chatMessages.appendChild(container);
            }

            // ── Events ─────────────────────────────────────────────

            backBtn.addEventListener('click', deselectChat);

            window.addEventListener('hashchange', function () {
                var hashId = getHashChatId();
                if (hashId && hashId !== activeChatId) {
                    selectChat(hashId);
                } else if (!hashId && activeChatId) {
                    deselectChat();
                }
            });

            // ── Init ───────────────────────────────────────────────

            loadChats();
        })();
        </script>
        <?php
    }
}
