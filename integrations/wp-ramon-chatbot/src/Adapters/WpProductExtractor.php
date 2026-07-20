<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Adapters;

use Ramon\Chatbot\Domain\ProductData;
use Ramon\Chatbot\Ports\ProductExtractor;

/**
 * WooCommerce implementation of ProductExtractor.
 *
 * Extracts product data from a WooCommerce product object.
 */
final class WpProductExtractor implements ProductExtractor
{
    public function extract(int $productId): ?ProductData
    {
        $product = \wc_get_product($productId);
        if (!$product instanceof \WC_Product) {
            return null;
        }

        $imageId = $product->get_image_id();
        $imageUrl = '';
        if ($imageId) {
            $imageUrl = (string) \wp_get_attachment_url($imageId);
        }

        $terms = \get_the_terms($productId, 'product_cat');
        $categories = '';
        if ($terms && !\is_wp_error($terms)) {
            $categories = \implode(',', \array_map(
                static fn(\stdClass $t): string => $t->name,
                $terms,
            ));
        }

        return new ProductData(
            productId: (string) $productId,
            sku: $product->get_sku() ?: '',
            name: $product->get_name(),
            description: $product->get_description(),
            categories: $categories,
            price: (float) $product->get_price(),
            stock: (int) $product->get_stock_quantity(),
            inStock: $product->get_stock_status() === 'instock',
            url: (string) (\get_permalink($productId) ?: ''),
            imageUrl: $imageUrl,
            status: $product->get_status(),
        );
    }
}
