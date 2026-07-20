<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Tests\Mocks;

use Ramon\Chatbot\Ports\OptionStore;

/**
 * In-memory mock for OptionStore.
 */
final class MockOptionStore implements OptionStore
{
    /** @var array<string, mixed> */
    private array $store = [];

    public function get(string $key, mixed $default = ''): mixed
    {
        return $this->store[$key] ?? $default;
    }

    public function set(string $key, mixed $value): void
    {
        $this->store[$key] = $value;
    }

    public function delete(string $key): void
    {
        unset($this->store[$key]);
    }

    /**
     * Check if an option was set.
     */
    public function has(string $key): bool
    {
        return \array_key_exists($key, $this->store);
    }

    /**
     * Get all stored options.
     *
     * @return array<string, mixed>
     */
    public function all(): array
    {
        return $this->store;
    }

    /**
     * Bulk-set options for testing.
     *
     * @param array<string, mixed> $data
     */
    public function load(array $data): void
    {
        $this->store = \array_merge($this->store, $data);
    }
}
