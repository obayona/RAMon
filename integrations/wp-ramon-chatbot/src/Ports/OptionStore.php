<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Ports;

/**
 * Abstraction for reading and writing key-value options.
 *
 * Decouples business logic from WordPress get_option / update_option,
 * making the code testable without a WP environment.
 */
interface OptionStore
{
    /**
     * Retrieve an option value.
     *
     * @param string $key     Option name.
     * @param mixed  $default Default value when key is missing.
     * @return mixed
     */
    public function get(string $key, mixed $default = ''): mixed;

    /**
     * Write an option value.
     *
     * @param string $key   Option name.
     * @param mixed  $value Value to store.
     */
    public function set(string $key, mixed $value): void;

    /**
     * Delete an option.
     *
     * @param string $key Option name.
     */
    public function delete(string $key): void;
}
