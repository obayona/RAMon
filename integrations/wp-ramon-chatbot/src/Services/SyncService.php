<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Services;

use Ramon\Chatbot\Ports\HttpClient;
use Ramon\Chatbot\Ports\OptionStore;

/**
 * Sends product sync changes to the backend API.
 *
 * Stateless service — receives all dependencies through constructor injection.
 */
final class SyncService
{
    public function __construct(
        private readonly OptionStore $options,
        private readonly HttpClient $http,
        private readonly JwtService $jwt,
    ) {
    }

    /**
     * Send a batch of product changes to the backend.
     *
     * @param array<int, array{action: string, product_id: string, fields: array}> $changes
     * @return array{success: bool, data?: array, error?: string}
     */
    public function send(array $changes): array
    {
        $apiUrl = \rtrim((string) $this->options->get('ramon_api_url', ''), '/');
        $token = $this->jwt->generate(3600);

        if ($apiUrl === '' || $token === '') {
            return ['success' => false, 'error' => 'API URL or token not configured'];
        }

        $endpoint = "{$apiUrl}/api/sync/products";
        $body = (string) \json_encode(['changes' => $changes], \JSON_THROW_ON_ERROR);

        $response = $this->http->post(
            $endpoint,
            [
                'Content-Type' => 'application/json',
                'Authorization' => "Bearer {$token}",
            ],
            $body,
            15,
        );

        if ($response['code'] >= 200 && $response['code'] < 300) {
            $data = \json_decode($response['body'], true);
            return ['success' => true, 'data' => $data ?? []];
        }

        return [
            'success' => false,
            'error' => "HTTP {$response['code']}: {$response['body']}",
        ];
    }
}
