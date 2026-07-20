<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Domain;

/**
 * Immutable value object representing initial sync status.
 */
final class SyncStatus
{
    public const STATUS_IDLE = 'idle';
    public const STATUS_RUNNING = 'running';
    public const STATUS_COMPLETE = 'complete';

    public function __construct(
        public readonly string $status,
        public readonly int $total,
        public readonly int $done,
        public readonly int $errors,
        public readonly int $percentage,
        public readonly string $time,
        public readonly bool $needsSync,
    ) {
    }

    /**
     * Build from raw option values.
     */
    public static function fromOptions(string $status, int $total, int $done, int $errors, string $time, bool $needsSync): self
    {
        $percentage = $total > 0 ? (int) round(($done + $errors) / $total * 100) : 0;

        return new self(
            status: $status,
            total: $total,
            done: $done,
            errors: $errors,
            percentage: min($percentage, 100),
            time: $time,
            needsSync: $needsSync,
        );
    }
}
