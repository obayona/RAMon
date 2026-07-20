<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Adapters;

use Ramon\Chatbot\Ports\CronScheduler;

/**
 * WordPress implementation of CronScheduler.
 *
 * Wraps WordPress cron functions.
 */
final class WpCronScheduler implements CronScheduler
{
    public function isScheduled(string $hook): bool
    {
        return \wp_next_scheduled($hook) !== false;
    }

    public function schedule(string $hook, int $timestamp, string $recurrence): void
    {
        \wp_schedule_event($timestamp, $recurrence, $hook);
    }

    public function unschedule(int $timestamp, string $hook): void
    {
        \wp_unschedule_event($timestamp, $hook);
    }

    /**
     * @return int|false
     */
    public function getNextTimestamp(string $hook): int|false
    {
        return \wp_next_scheduled($hook);
    }
}
