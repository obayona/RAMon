<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Tests\Unit\Services;

use PHPUnit\Framework\TestCase;
use Ramon\Chatbot\Services\JwtService;
use Ramon\Chatbot\Tests\Mocks\MockOptionStore;

final class JwtServiceTest extends TestCase
{
    private MockOptionStore $options;
    private JwtService $jwt;

    protected function setUp(): void
    {
        $this->options = new MockOptionStore();
        $this->jwt = new JwtService($this->options);
    }

    public function testGenerateReturnsEmptyStringWhenNoAppKey(): void
    {
        $token = $this->jwt->generate();

        $this->assertSame('', $token);
    }

    public function testGenerateReturnsValidJwtFormat(): void
    {
        $this->options->set('ramon_app_key', 'test-secret-key');

        $token = $this->jwt->generate();

        $parts = \explode('.', $token);
        $this->assertCount(3, $parts, 'JWT should have 3 parts separated by dots');
    }

    public function testGenerateWithoutExpiry(): void
    {
        $this->options->set('ramon_app_key', 'test-secret-key');

        $token = $this->jwt->generate(0);

        $parts = \explode('.', $token);
        $payload = \json_decode(\base64_decode($parts[1]), true);

        $this->assertArrayHasKey('iat', $payload);
        $this->assertArrayNotHasKey('exp', $payload);
    }

    public function testGenerateWithExpiry(): void
    {
        $this->options->set('ramon_app_key', 'test-secret-key');

        $token = $this->jwt->generate(3600);

        $parts = \explode('.', $token);
        $payload = \json_decode(\base64_decode($parts[1]), true);

        $this->assertArrayHasKey('exp', $payload);
        $this->assertSame($payload['iat'] + 3600, $payload['exp']);
    }

    public function testGenerateProducesConsistentTokensForSameInput(): void
    {
        $this->options->set('ramon_app_key', 'test-secret-key');

        $token1 = $this->jwt->generate(0);
        $token2 = $this->jwt->generate(0);

        $this->assertSame($token1, $token2);
    }

    public function testDifferentKeysProduceDifferentTokens(): void
    {
        $this->options->set('ramon_app_key', 'key-one');
        $token1 = $this->jwt->generate(0);

        $this->options->set('ramon_app_key', 'key-two');
        $token2 = $this->jwt->generate(0);

        $this->assertNotSame($token1, $token2);
    }
}
