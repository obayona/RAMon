<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Adapters;

use Ramon\Chatbot\Ports\OptionStore;

/**
 * WordPress implementation of OptionStore.
 *
 * Wraps get_option / update_option / delete_option.
 */
final class WpOptionStore implements OptionStore
{
    public function get(string $key, mixed $default = ''): mixed
    {
        return \get_option($key, $default);
    }

    public function set(string $key, mixed $value): void
    {
        \update_option($key, $value);
    }

    public function delete(string $key): void
    {
        \delete_option($key);
    }
}
