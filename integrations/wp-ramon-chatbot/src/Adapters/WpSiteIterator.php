<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Adapters;

use Ramon\Chatbot\Ports\SiteIterator;

/**
 * WordPress implementation of SiteIterator.
 *
 * Wraps get_sites / switch_to_blog / restore_current_blog for multisite support.
 */
final class WpSiteIterator implements SiteIterator
{
    public function forEachSite(callable $callback): void
    {
        if (!\is_multisite()) {
            $callback();
            return;
        }

        $sites = \get_sites(['fields' => 'ids']);
        foreach ($sites as $siteId) {
            \switch_to_blog($siteId);
            $callback();
            \restore_current_blog();
        }
    }
}
