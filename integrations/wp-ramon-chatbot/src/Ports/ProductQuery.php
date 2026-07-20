<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Ports;

/**
 * Abstraction for querying published WooCommerce products.
 *
 * Decouples business logic from WP_Query,
 * making the code testable without a WP environment.
 */
interface ProductQuery
{
    /**
     * Count all published products.
     */
    public function countPublished(): int;

    /**
     * Fetch published product IDs for a specific page.
     *
     * @param int $page    1-based page number.
     * @param int $perPage Items per page.
     *
     * @return list<int> Product IDs.
     */
    public function fetchProductIds(int $page, int $perPage): array;
}
