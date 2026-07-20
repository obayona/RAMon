<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Adapters;

use Ramon\Chatbot\Ports\HttpClient;

/**
 * WordPress implementation of HttpClient.
 *
 * Wraps wp_remote_post and standardizes the response format.
 */
final class WpHttpClient implements HttpClient
{
    public function post(string $url, array $headers, string $body, int $timeout = 15): array
    {
        $response = \wp_remote_post($url, [
            'headers' => $headers,
            'body' => $body,
            'timeout' => $timeout,
        ]);

        if (\is_wp_error($response)) {
            return [
                'code' => 0,
                'body' => $response->get_error_message(),
            ];
        }

        return [
            'code' => (int) \wp_remote_retrieve_response_code($response),
            'body' => (string) \wp_remote_retrieve_body($response),
        ];
    }
}
