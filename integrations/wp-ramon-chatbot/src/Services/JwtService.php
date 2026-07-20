<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Services;

use Ramon\Chatbot\Ports\OptionStore;

/**
 * JWT token generation using HMAC-SHA256.
 *
 * Stateless service — no WP dependency. Receives the app key
 * through the OptionStore interface.
 */
final class JwtService
{
    public function __construct(
        private readonly OptionStore $options,
    ) {
    }

    /**
     * Generate a JWT token.
     *
     * @param int $expiresIn Seconds until expiry. 0 = no expiry.
     * @return string Encoded JWT, or empty string if app key is missing.
     */
    public function generate(int $expiresIn = 0): string
    {
        $appKey = (string) $this->options->get('ramon_app_key', '');
        if ($appKey === '') {
            return '';
        }

        $claims = ['iat' => $this->now()];
        if ($expiresIn > 0) {
            $claims['exp'] = $this->now() + $expiresIn;
        }

        $header = $this->base64UrlEncode((string) \json_encode(['alg' => 'HS256', 'typ' => 'JWT']));
        $payload = $this->base64UrlEncode((string) \json_encode($claims));
        $signature = $this->base64UrlEncode(
            \hash_hmac('sha256', "{$header}.{$payload}", $appKey, true),
        );

        return "{$header}.{$payload}.{$signature}";
    }

    /**
     * Base64url-encode raw data (RFC 7515 §2).
     */
    private function base64UrlEncode(string $data): string
    {
        return \rtrim(\strtr(\base64_encode($data), '+/', '-_'), '=');
    }

    /**
     * Return current Unix timestamp. Extracted for testability.
     */
    private function now(): int
    {
        return \time();
    }
}
