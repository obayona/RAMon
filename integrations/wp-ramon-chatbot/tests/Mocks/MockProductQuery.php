<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Tests\Mocks;

use Ramon\Chatbot\Ports\ProductQuery;

/**
 * In-memory mock for ProductQuery.
 *
 * Pre-load product IDs to simulate a WooCommerce product catalog.
 */
final class MockProductQuery implements ProductQuery
{
    /** @var list<int> */
    private array $productIds = [];

    /**
     * Set the full list of published product IDs.
     *
     * @param list<int> $ids
     */
    public function setProducts(array $ids): void
    {
        $this->productIds = $ids;
    }

    public function countPublished(): int
    {
        return \count($this->productIds);
    }

    /**
     * @return list<int>
     */
    public function fetchProductIds(int $page, int $perPage): array
    {
        $offset = ($page - 1) * $perPage;
        return \array_values(\array_slice($this->productIds, $offset, $perPage));
    }
}
