<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Tests\Mocks;

use Ramon\Chatbot\Domain\ProductData;
use Ramon\Chatbot\Ports\ProductExtractor;

/**
 * In-memory mock for ProductExtractor.
 *
 * Returns pre-configured ProductData objects by ID.
 */
final class MockProductExtractor implements ProductExtractor
{
    /** @var array<int, ProductData> */
    private array $products = [];

    /**
     * Register a product for extraction.
     */
    public function addProduct(int $id, ProductData $product): void
    {
        $this->products[$id] = $product;
    }

    /**
     * Bulk-set products for extraction.
     *
     * @param array<int, ProductData> $products
     */
    public function setProducts(array $products): void
    {
        $this->products = $products;
    }

    public function extract(int $productId): ?ProductData
    {
        return $this->products[$productId] ?? null;
    }

    /**
     * Get the number of products registered.
     */
    public function count(): int
    {
        return \count($this->products);
    }
}
