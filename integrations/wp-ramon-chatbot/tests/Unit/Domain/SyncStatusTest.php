<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Tests\Unit\Domain;

use PHPUnit\Framework\TestCase;
use Ramon\Chatbot\Domain\SyncStatus;

final class SyncStatusTest extends TestCase
{
    public function testFromOptionsCalculatesPercentage(): void
    {
        $status = SyncStatus::fromOptions(
            status: 'running',
            total: 200,
            done: 50,
            errors: 10,
            time: '2024-01-15 12:00:00',
            needsSync: false,
        );

        $this->assertSame('running', $status->status);
        $this->assertSame(200, $status->total);
        $this->assertSame(50, $status->done);
        $this->assertSame(10, $status->errors);
        // (50 + 10) / 200 * 100 = 30%
        $this->assertSame(30, $status->percentage);
        $this->assertSame('2024-01-15 12:00:00', $status->time);
        $this->assertFalse($status->needsSync);
    }

    public function testFromOptionsZeroTotal(): void
    {
        $status = SyncStatus::fromOptions(
            status: 'idle',
            total: 0,
            done: 0,
            errors: 0,
            time: '',
            needsSync: true,
        );

        $this->assertSame(0, $status->percentage);
        $this->assertTrue($status->needsSync);
    }

    public function testFromOptionsClampsTo100(): void
    {
        $status = SyncStatus::fromOptions(
            status: 'complete',
            total: 10,
            done: 10,
            errors: 5,
            time: '2024-01-15 12:00:00',
            needsSync: false,
        );

        // (10 + 5) / 10 * 100 = 150% → clamped to 100%
        $this->assertSame(100, $status->percentage);
    }

    public function testStatusConstants(): void
    {
        $this->assertSame('idle', SyncStatus::STATUS_IDLE);
        $this->assertSame('running', SyncStatus::STATUS_RUNNING);
        $this->assertSame('complete', SyncStatus::STATUS_COMPLETE);
    }
}
