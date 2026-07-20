<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Tests\Mocks;

use Ramon\Chatbot\Ports\CronScheduler;

/**
 * In-memory mock for CronScheduler.
 *
 * Tracks scheduled hooks and timestamps for test assertions.
 */
final class MockCronScheduler implements CronScheduler
{
    /** @var array<string, list<int>> */
    private array $scheduled = [];

    public function isScheduled(string $hook): bool
    {
        return isset($this->scheduled[$hook]) && $this->scheduled[$hook] !== [];
    }

    public function schedule(string $hook, int $timestamp, string $recurrence): void
    {
        $this->scheduled[$hook][] = $timestamp;
    }

    public function unschedule(int $timestamp, string $hook): void
    {
        if (isset($this->scheduled[$hook])) {
            $this->scheduled[$hook] = \array_values(
                \array_filter($this->scheduled[$hook], static fn(int $ts): bool => $ts !== $timestamp),
            );
        }
    }

    /**
     * @return int|false
     */
    public function getNextTimestamp(string $hook): int|false
    {
        if (!isset($this->scheduled[$hook]) || $this->scheduled[$hook] === []) {
            return false;
        }

        return \reset($this->scheduled[$hook]);
    }

    /**
     * Get all scheduled hooks and their timestamps.
     *
     * @return array<string, list<int>>
     */
    public function getScheduled(): array
    {
        return $this->scheduled;
    }
}
