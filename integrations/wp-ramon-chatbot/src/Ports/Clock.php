<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Ports;

/**
 * Abstraction for reading the current time.
 *
 * Decouples business logic from WordPress time functions,
 * making the code testable with a deterministic clock.
 */
interface Clock
{
    /**
     * Get the current Unix timestamp.
     */
    public function now(): int;

    /**
     * Get the current time formatted for MySQL.
     *
     * @return string Datetime string in MySQL format.
     */
    public function mysql(): string;
}
