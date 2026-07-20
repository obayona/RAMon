<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Tests\Mocks;

use Ramon\Chatbot\Ports\SiteIterator;

/**
 * In-memory mock for SiteIterator.
 *
 * Simulates multisite iteration with configurable site IDs.
 */
final class MockSiteIterator implements SiteIterator
{
    /** @var list<int> */
    private array $siteIds = [1];

    /** @var list<callable()> */
    private array $invocations = [];

    /**
     * Set the site IDs to iterate over.
     *
     * @param list<int> $ids
     */
    public function setSiteIds(array $ids): void
    {
        $this->siteIds = $ids;
    }

    public function forEachSite(callable $callback): void
    {
        foreach ($this->siteIds as $_siteId) {
            $callback();
            $this->invocations[] = $callback;
        }
    }

    /**
     * Get the number of times the callback was invoked.
     */
    public function getInvocationCount(): int
    {
        return \count($this->invocations);
    }
}
