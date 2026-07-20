<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Ports;

/**
 * Abstraction for temporary key-value storage.
 *
 * Decouples business logic from WordPress transient functions,
 * making the code testable without a WP environment.
 */
interface TransientStore
{
    /**
     * Retrieve a transient value.
     *
     * @param string $key Transient name.
     * @return mixed Stored value or false if not found.
     */
    public function get(string $key): mixed;

    /**
     * Store a transient value.
     *
     * @param string $key        Transient name.
     * @param mixed  $value      Value to store.
     * @param int    $ttlSeconds Time-to-live in seconds.
     */
    public function set(string $key, mixed $value, int $ttlSeconds): void;

    /**
     * Delete a transient.
     *
     * @param string $key Transient name.
     */
    public function delete(string $key): void;
}
