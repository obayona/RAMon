<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Adapters;

use Ramon\Chatbot\Ports\TransientStore;

/**
 * WordPress implementation of TransientStore.
 *
 * Wraps set_transient / get_transient / delete_transient.
 */
final class WpTransientStore implements TransientStore
{
    public function get(string $key): mixed
    {
        return \get_transient($key);
    }

    public function set(string $key, mixed $value, int $ttlSeconds): void
    {
        \set_transient($key, $value, $ttlSeconds);
    }

    public function delete(string $key): void
    {
        \delete_transient($key);
    }
}
