<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Ports;

use Ramon\Chatbot\Domain\ProductData;

/**
 * Abstraction for extracting product data from WooCommerce.
 *
 * Decouples the sync logic from WC's product API,
 * making the code testable without a WooCommerce installation.
 */
interface ProductExtractor
{
    /**
     * Extract product data by ID.
     *
     * @param int $productId WordPress post ID.
     * @return ProductData|null Null if product not found.
     */
    public function extract(int $productId): ?ProductData;
}
