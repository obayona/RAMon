<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Sync;

use Ramon\Chatbot\Domain\ProductData;
use Ramon\Chatbot\Ports\Clock;
use Ramon\Chatbot\Ports\OptionStore;
use Ramon\Chatbot\Ports\ProductExtractor;
use Ramon\Chatbot\Services\SyncService;

/**
 * Handles real-time WooCommerce product change events.
 *
 * Registered as a WC hook handler. Extracts product data and
 * sends it to the backend via SyncService.
 */
final class ProductChangeHandler
{
    public function __construct(
        private readonly ProductExtractor $extractor,
        private readonly SyncService $sync,
        private readonly OptionStore $options,
        private readonly Clock $clock,
    ) {
    }

    /**
     * Handle product create/update — send an upsert.
     *
     * @param int         $productId WordPress post ID.
     * @param \WC_Product $product   WooCommerce product object.
     */
    public function onProductChange(int $productId, \WC_Product $product = null): void
    {
        if (\get_post_type($productId) !== 'product') {
            return;
        }

        $data = $this->extractor->extract($productId);
        if ($data === null) {
            return;
        }

        $this->sync->send([[
            'action' => 'upsert',
            'product_id' => $data->productId,
            'fields' => $data->toArray(),
        ]]);

        $this->options->set('ramon_sync_last_change', $this->clock->mysql());
    }

    /**
     * Handle product deletion — send a delete.
     *
     * @param int $productId WordPress post ID.
     */
    public function onProductDelete(int $productId): void
    {
        if (\get_post_type($productId) !== 'product') {
            return;
        }

        $this->sync->send([[
            'action' => 'delete',
            'product_id' => (string) $productId,
            'fields' => [],
        ]]);

        $this->options->set('ramon_sync_last_change', $this->clock->mysql());
    }
}
