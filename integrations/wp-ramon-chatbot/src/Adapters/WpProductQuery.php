<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Adapters;

use Ramon\Chatbot\Ports\ProductQuery;

/**
 * WordPress implementation of ProductQuery.
 *
 * Wraps WP_Query to fetch published product IDs.
 */
final class WpProductQuery implements ProductQuery
{
    public function countPublished(): int
    {
        $query = new \WP_Query([
            'post_type' => 'product',
            'post_status' => 'publish',
            'posts_per_page' => 1,
            'fields' => 'ids',
            'update_post_meta_cache' => false,
            'update_post_term_cache' => false,
        ]);

        return $query->found_posts;
    }

    /**
     * @return list<int>
     */
    public function fetchProductIds(int $page, int $perPage): array
    {
        $query = new \WP_Query([
            'post_type' => 'product',
            'post_status' => 'publish',
            'posts_per_page' => $perPage,
            'paged' => $page,
            'fields' => 'ids',
            'update_post_meta_cache' => false,
            'update_post_term_cache' => false,
        ]);

        $ids = \array_map('intval', $query->posts);
        \wp_reset_postdata();

        return $ids;
    }
}
