<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Ports;

/**
 * Abstraction for WP-Cron scheduling.
 *
 * Decouples business logic from WordPress cron functions,
 * making the code testable without a WP runtime.
 */
interface CronScheduler
{
    /**
     * Check if a cron event is scheduled.
     */
    public function isScheduled(string $hook): bool;

    /**
     * Schedule a recurring cron event.
     */
    public function schedule(string $hook, int $timestamp, string $recurrence): void;

    /**
     * Unschedule a specific cron event by timestamp.
     */
    public function unschedule(int $timestamp, string $hook): void;

    /**
     * Get the next scheduled timestamp for a hook.
     *
     * @return int|false Unix timestamp or false if not scheduled.
     */
    public function getNextTimestamp(string $hook): int|false;
}
