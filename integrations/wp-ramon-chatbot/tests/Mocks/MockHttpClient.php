<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Tests\Mocks;

use Ramon\Chatbot\Ports\HttpClient;

/**
 * In-memory mock for HttpClient.
 *
 * Records all requests and returns pre-configured responses.
 */
final class MockHttpClient implements HttpClient
{
    /** @var list<array{url: string, headers: array, body: string, timeout: int}> */
    private array $requests = [];

    private int $responseCode = 200;

    private string $responseBody = '{}';

    /**
     * Configure the response for subsequent requests.
     */
    public function setResponse(int $code, string $body): void
    {
        $this->responseCode = $code;
        $this->responseBody = $body;
    }

    public function post(string $url, array $headers, string $body, int $timeout = 15): array
    {
        $this->requests[] = [
            'url' => $url,
            'headers' => $headers,
            'body' => $body,
            'timeout' => $timeout,
        ];

        return [
            'code' => $this->responseCode,
            'body' => $this->responseBody,
        ];
    }

    /**
     * Get all recorded requests.
     *
     * @return list<array{url: string, headers: array, body: string, timeout: int}>
     */
    public function getRequests(): array
    {
        return $this->requests;
    }

    /**
     * Get the last recorded request.
     */
    public function getLastRequest(): ?array
    {
        return $this->requests[\count($this->requests) - 1] ?? null;
    }

    /**
     * Get the number of requests made.
     */
    public function getRequestCount(): int
    {
        return \count($this->requests);
    }
}
