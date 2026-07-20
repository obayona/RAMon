<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Adapters;

use Ramon\Chatbot\Ports\Clock;

/**
 * WordPress implementation of Clock.
 *
 * Wraps WordPress time functions.
 */
final class WpClock implements Clock
{
    public function now(): int
    {
        return \time();
    }

    public function mysql(): string
    {
        return (string) \current_time('mysql');
    }
}
