<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Tests\Mocks;

use Ramon\Chatbot\Ports\Clock;

/**
 * Deterministic mock for Clock.
 *
 * Returns a fixed time that can be configured for tests.
 */
final class MockClock implements Clock
{
    private int $timestamp;

    public function __construct(int $timestamp = 1700000000)
    {
        $this->timestamp = $timestamp;
    }

    public function now(): int
    {
        return $this->timestamp;
    }

    public function mysql(): string
    {
        return \date('Y-m-d H:i:s', $this->timestamp);
    }

    /**
     * Set the current timestamp.
     */
    public function setTimestamp(int $timestamp): void
    {
        $this->timestamp = $timestamp;
    }
}
