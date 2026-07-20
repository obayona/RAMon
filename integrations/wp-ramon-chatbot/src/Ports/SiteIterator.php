<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Ports;

/**
 * Abstraction for iterating over WordPress multisite sites.
 *
 * Decouples business logic from get_sites / switch_to_blog /
 * restore_current_blog, making the code testable without a WP environment.
 */
interface SiteIterator
{
    /**
     * Execute a callback for each site in the network.
     *
     * On single-site installs the callback runs once without switching.
     *
     * @param callable(): void $callback Function to invoke per site.
     */
    public function forEachSite(callable $callback): void;
}
