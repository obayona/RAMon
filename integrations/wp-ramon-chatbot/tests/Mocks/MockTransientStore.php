<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Tests\Mocks;

use Ramon\Chatbot\Ports\TransientStore;

/**
 * In-memory mock for TransientStore.
 */
final class MockTransientStore implements TransientStore
{
    /** @var array<string, mixed> */
    private array $store = [];

    public function get(string $key): mixed
    {
        return $this->store[$key] ?? false;
    }

    public function set(string $key, mixed $value, int $ttlSeconds): void
    {
        $this->store[$key] = $value;
    }

    public function delete(string $key): void
    {
        unset($this->store[$key]);
    }

    /**
     * Check if a transient exists.
     */
    public function has(string $key): bool
    {
        return \array_key_exists($key, $this->store);
    }

    /**
     * Get all stored transients.
     *
     * @return array<string, mixed>
     */
    public function all(): array
    {
        return $this->store;
    }
}
