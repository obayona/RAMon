<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Tests\Unit\Services;

use PHPUnit\Framework\TestCase;
use Ramon\Chatbot\Services\JwtService;
use Ramon\Chatbot\Services\SyncService;
use Ramon\Chatbot\Tests\Mocks\MockHttpClient;
use Ramon\Chatbot\Tests\Mocks\MockOptionStore;

final class SyncServiceTest extends TestCase
{
    private MockOptionStore $options;
    private MockHttpClient $http;
    private SyncService $sync;

    protected function setUp(): void
    {
        $this->options = new MockOptionStore();
        $this->http = new MockHttpClient();
        $jwt = new JwtService($this->options);
        $this->sync = new SyncService($this->options, $this->http, $jwt);
    }

    public function testSendFailsWhenApiUrlMissing(): void
    {
        $this->options->set('ramon_app_key', 'key');
        // ramon_api_url not set

        $result = $this->sync->send([[
            'action' => 'upsert',
            'product_id' => '1',
            'fields' => [],
        ]]);

        $this->assertFalse($result['success']);
        $this->assertStringContainsString('API URL', $result['error']);
        $this->assertSame(0, $this->http->getRequestCount());
    }

    public function testSendFailsWhenAppKeyMissing(): void
    {
        $this->options->set('ramon_api_url', 'https://api.example.com');
        // ramon_app_key not set → token is empty

        $result = $this->sync->send([[
            'action' => 'upsert',
            'product_id' => '1',
            'fields' => [],
        ]]);

        $this->assertFalse($result['success']);
        $this->assertStringContainsString('token', $result['error']);
    }

    public function testSendSuccessOn200(): void
    {
        $this->options->load([
            'ramon_api_url' => 'https://api.example.com',
            'ramon_app_key' => 'test-key',
        ]);
        $this->http->setResponse(200, '{"queued": 1}');

        $result = $this->sync->send([[
            'action' => 'upsert',
            'product_id' => '42',
            'fields' => ['name' => 'GPU'],
        ]]);

        $this->assertTrue($result['success']);
        $this->assertSame(['queued' => 1], $result['data']);
    }

    public function testSendFailureOn500(): void
    {
        $this->options->load([
            'ramon_api_url' => 'https://api.example.com',
            'ramon_app_key' => 'test-key',
        ]);
        $this->http->setResponse(500, 'Internal Server Error');

        $result = $this->sync->send([[
            'action' => 'upsert',
            'product_id' => '42',
            'fields' => [],
        ]]);

        $this->assertFalse($result['success']);
        $this->assertStringContainsString('500', $result['error']);
    }

    public function testSendCorrectEndpoint(): void
    {
        $this->options->load([
            'ramon_api_url' => 'https://api.example.com',
            'ramon_app_key' => 'test-key',
        ]);
        $this->http->setResponse(200, '{}');

        $this->sync->send([[
            'action' => 'delete',
            'product_id' => '99',
            'fields' => [],
        ]]);

        $request = $this->http->getLastRequest();
        $this->assertSame('https://api.example.com/api/sync/products', $request['url']);
    }

    public function testSendSendsBearerToken(): void
    {
        $this->options->load([
            'ramon_api_url' => 'https://api.example.com',
            'ramon_app_key' => 'test-key',
        ]);
        $this->http->setResponse(200, '{}');

        $this->sync->send([[
            'action' => 'upsert',
            'product_id' => '1',
            'fields' => [],
        ]]);

        $request = $this->http->getLastRequest();
        $this->assertArrayHasKey('Authorization', $request['headers']);
        $this->assertStringStartsWith('Bearer ', $request['headers']['Authorization']);
    }

    public function testSendStripsTrailingSlash(): void
    {
        $this->options->load([
            'ramon_api_url' => 'https://api.example.com/',
            'ramon_app_key' => 'test-key',
        ]);
        $this->http->setResponse(200, '{}');

        $this->sync->send([[
            'action' => 'upsert',
            'product_id' => '1',
            'fields' => [],
        ]]);

        $request = $this->http->getLastRequest();
        $this->assertSame('https://api.example.com/api/sync/products', $request['url']);
    }
}
