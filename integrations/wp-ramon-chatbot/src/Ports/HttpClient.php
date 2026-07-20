<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Ports;

/**
 * Abstraction for making HTTP requests.
 *
 * Decouples business logic from wp_remote_post / wp_remote_get,
 * making the code testable without a WP environment.
 */
interface HttpClient
{
    /**
     * Send a POST request.
     *
     * @param string $url     Target URL.
     * @param array  $headers Key-value header pairs.
     * @param string $body    Raw request body.
     * @param int    $timeout Timeout in seconds.
     * @return array{code: int, body: string} Response data.
     */
    public function post(string $url, array $headers, string $body, int $timeout = 15): array;
}
