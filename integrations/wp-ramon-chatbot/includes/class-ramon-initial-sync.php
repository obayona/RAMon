<?php
/**
 * Initial product sync — OOP implementation.
 *
 * On plugin activation, populates a temporary table with all published
 * WooCommerce product IDs. A WP-Cron job then processes them in batches,
 * sending each batch to the backend API. The table is dropped once
 * all products have been synced.
 */

if (!defined('ABSPATH')) {
    exit;
}

class RAMon_Initial_Sync {

    /** @var self|null Singleton instance. */
    private static ?self $instance = null;

    /** @var string Sync queue table name (with WP prefix). */
    private string $table;

    /** @var int Batch size per cron invocation. */
    private int $batch_size = 10;

    /** @var string Cron hook name. */
    const CRON_HOOK = 'ramon_initial_sync_hook';

    /** @var string Option prefix for sync status. */
    const OPT_PREFIX = 'ramon_initial_sync_';

    private function __construct() {
        global $wpdb;
        $this->table = $wpdb->prefix . 'ramon_initial_sync';
    }

    /**
     * Get the singleton instance.
     */
    public static function instance(): self {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    // ------------------------------------------------------------------
    // Activation
    // ------------------------------------------------------------------

    /**
     * Handle plugin activation — set a flag, no heavy work.
     *
     * @param bool $network_wide Whether the plugin was network-activated.
     */
    public function on_activate( bool $network_wide ): void {
        if ( $network_wide ) {
            $sites = get_sites( [ 'fields' => 'ids' ] );
            foreach ( $sites as $site_id ) {
                switch_to_blog( $site_id );
                $this->flag_activation();
                restore_current_blog();
            }
        } else {
            $this->flag_activation();
        }
    }

    /**
     * Handle plugin deactivation — clean up cron.
     */
    public function on_deactivate(): void {
        $this->unschedule_cron();
        delete_option( self::OPT_PREFIX . 'locked' );
    }

    // ------------------------------------------------------------------
    // Cron
    // ------------------------------------------------------------------

    /**
     * Schedule the cron event if not already scheduled.
     */
    public function schedule_cron(): void {
        if ( ! wp_next_scheduled( self::CRON_HOOK ) ) {
            wp_schedule_event( time(), 'one_minute', self::CRON_HOOK );
        }
    }

    /**
     * Unschedule the cron event.
     */
    public function unschedule_cron(): void {
        $timestamp = wp_next_scheduled( self::CRON_HOOK );
        if ( $timestamp ) {
            wp_unschedule_event( $timestamp, self::CRON_HOOK );
        }
    }

    /**
     * Main cron callback — orchestrates the entire initial sync.
     *
     * Called every minute by WP-Cron. On the first invocation it creates
     * the table and populates it. On subsequent invocations it processes
     * one batch of pending products. Once all products are synced the
     * cron is unscheduled and the table is dropped.
     */
    public function process_cron(): void {
        // Only run if initial sync is needed
        if ( get_option( self::OPT_PREFIX . 'status' ) !== 'running' ) {
            return;
        }

        // Prevent overlapping cron executions
        if ( get_option( self::OPT_PREFIX . 'locked', false ) ) {
            return;
        }
        update_option( self::OPT_PREFIX . 'locked', true );

        try {
            if ( ! $this->table_exists() ) {
                $this->create_and_populate_table();
            }

            $result = $this->process_batch();

            if ( $result['pending'] === 0 ) {
                $this->finalize();
            }
        } finally {
            delete_option( self::OPT_PREFIX . 'locked' );
        }
    }

    // ------------------------------------------------------------------
    // Table lifecycle
    // ------------------------------------------------------------------

    /**
     * Check whether the sync queue table exists.
     */
    private function table_exists(): bool {
        global $wpdb;
        $escaped = esc_sql( $this->table );
        // phpcs:ignore WordPress.DB.DirectDatabaseQuery
        $result = $wpdb->get_var(
            "SELECT TABLE_NAME FROM information_schema.TABLES
             WHERE TABLE_SCHEMA = '{$wpdb->dbname}' AND TABLE_NAME = '{$escaped}'"
        );
        return $result !== null;
    }

    /**
     * Create the sync queue table and populate it with all published
     * WooCommerce product IDs. Runs in a single request — paginated
     * WP_Query to avoid memory spikes.
     */
    private function create_and_populate_table(): void {
        global $wpdb;

        // phpcs:ignore WordPress.DB.DirectDatabaseQuery
        $wpdb->query(
            "CREATE TABLE IF NOT EXISTS {$this->table} (
                id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                product_id BIGINT UNSIGNED NOT NULL,
                status VARCHAR(10) NOT NULL DEFAULT 'pending',
                error TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                KEY idx_status (status)
            ) {$wpdb->get_charset_collate()}"
        );

        $args = [
            'post_type'      => 'product',
            'post_status'    => 'publish',
            'posts_per_page' => 100,
            'paged'          => 1,
            'fields'         => 'ids',
        ];

        $query  = new \WP_Query( $args );
        $total  = $query->found_posts;
        $pages  = $query->max_num_pages;

        $this->update_option( 'total', $total );
        $this->update_option( 'done', 0 );
        $this->update_option( 'errors', 0 );
        $this->update_option( 'time', current_time( 'mysql' ) );

        for ( $p = 1; $p <= $pages; $p++ ) {
            $args['paged'] = $p;
            $query    = new \WP_Query( $args );
            $products = $query->posts;

            foreach ( $products as $pid ) {
                // phpcs:ignore WordPress.DB.DirectDatabaseQuery
                $wpdb->insert( $this->table, [
                    'product_id' => $pid,
                    'status'     => 'pending',
                ], [ '%d', '%s' ] );
            }

            wp_reset_postdata();
        }
    }

    /**
     * Drop the sync queue table.
     */
    private function drop_table(): void {
        global $wpdb;
        // phpcs:ignore WordPress.DB.DirectDatabaseQuery
        $wpdb->query( "DROP TABLE IF EXISTS {$this->table}" );
    }

    // ------------------------------------------------------------------
    // Batch processing
    // ------------------------------------------------------------------

    /**
     * Process one batch of pending products.
     *
     * @return array{pending: int, processed: int, errors: int} Batch result.
     */
    private function process_batch(): array {
        global $wpdb;

        // Fetch pending product IDs
        // phpcs:ignore WordPress.DB.DirectDatabaseQuery
        $product_ids = $wpdb->get_col(
            $wpdb->prepare(
                "SELECT product_id FROM {$this->table}
                 WHERE status = 'pending'
                 ORDER BY id ASC
                 LIMIT %d",
                $this->batch_size
            )
        );

        if ( empty( $product_ids ) ) {
            return [ 'pending' => 0, 'processed' => 0, 'errors' => 0 ];
        }

        // Fetch live product data from WooCommerce
        $wc_products = wc_get_products( [
            'include' => array_map( 'intval', $product_ids ),
            'return'  => 'objects',
            'limit'   => count( $product_ids ),
        ] );

        $changes = [];
        foreach ( $wc_products as $product ) {
            $data = $this->extract_product_data( $product );
            if ( $data ) {
                $changes[] = [
                    'action'     => 'upsert',
                    'product_id' => $data['product_id'],
                    'fields'     => $data,
                ];
            }
        }

        $processed = 0;
        $errors    = 0;

        if ( ! empty( $changes ) ) {
            $result = $this->send_batch( $changes );

            if ( is_wp_error( $result ) ) {
                // Mark all as error
                $this->mark_status( $product_ids, 'error', $result->get_error_message() );
                $errors = count( $product_ids );
            } else {
                // Mark all as done
                $this->mark_status( $product_ids, 'done' );
                $processed = count( $product_ids );
            }
        }

        // Count remaining
        // phpcs:ignore WordPress.DB.DirectDatabaseQuery
        $pending = (int) $wpdb->get_var(
            "SELECT COUNT(*) FROM {$this->table} WHERE status = 'pending'"
        );

        // Update running totals
        $done_total  = (int) $this->get_option( 'done', 0 ) + $processed;
        $error_total = (int) $this->get_option( 'errors', 0 ) + $errors;

        $this->update_option( 'done', $done_total );
        $this->update_option( 'errors', $error_total );
        $this->update_option( 'time', current_time( 'mysql' ) );

        return [
            'pending'   => $pending,
            'processed' => $processed,
            'errors'    => $errors,
        ];
    }

    /**
     * Mark a set of product IDs with a given status.
     *
     * @param int[]    $ids    Product IDs to update.
     * @param string   $status New status value.
     * @param string[] $error  Optional error message.
     */
    private function mark_status( array $ids, string $status, string $error = '' ): void {
        global $wpdb;

        if ( empty( $ids ) ) {
            return;
        }

        $placeholders = implode( ',', array_fill( 0, count( $ids ), '%d' ) );

        if ( $error ) {
            // phpcs:ignore WordPress.DB.DirectDatabaseQuery
            $wpdb->query( $wpdb->prepare(
                "UPDATE {$this->table} SET status = %s, error = %s WHERE product_id IN ({$placeholders})",
                array_merge( [ $status, $error ], $ids )
            ) );
        } else {
            // phpcs:ignore WordPress.DB.DirectDatabaseQuery
            $wpdb->query( $wpdb->prepare(
                "UPDATE {$this->table} SET status = %s WHERE product_id IN ({$placeholders})",
                array_merge( [ $status ], $ids )
            ) );
        }
    }

    // ------------------------------------------------------------------
    // Finalization
    // ------------------------------------------------------------------

    /**
     * Mark initial sync as complete, unschedule cron, drop table.
     */
    private function finalize(): void {
        $this->update_option( 'status', 'complete' );
        $this->update_option( 'time', current_time( 'mysql' ) );
        $this->unschedule_cron();

        // Drop the table after a short delay (next page load)
        // Store a flag so admin_init can clean up
        set_transient( 'ramon_drop_initial_sync_table', true, 60 );
    }

    /**
     * Drop the initial sync table if flagged for cleanup.
     * Hooked to admin_init.
     */
    public function maybe_drop_table(): void {
        if ( get_transient( 'ramon_drop_initial_sync_table' ) ) {
            delete_transient( 'ramon_drop_initial_sync_table' );
            if ( $this->table_exists() ) {
                $this->drop_table();
            }
        }
    }

    // ------------------------------------------------------------------
    // Retry failed
    // ------------------------------------------------------------------

    /**
     * Reset all error rows back to pending so the next cron picks them up.
     *
     * @return int Number of rows reset.
     */
    public function retry_failed(): int {
        global $wpdb;

        // phpcs:ignore WordPress.DB.DirectDatabaseQuery
        $count = $wpdb->query(
            "UPDATE {$this->table} SET status = 'pending', error = NULL WHERE status = 'error'"
        );

        if ( $count ) {
            $this->update_option( 'errors', 0 );
            $this->update_option( 'time', current_time( 'mysql' ) );

            // Re-set status to running and ensure cron is scheduled
            $this->update_option( 'status', 'running' );
            $this->schedule_cron();
        }

        return (int) $count;
    }

    // ------------------------------------------------------------------
    // Status (for admin UI)
    // ------------------------------------------------------------------

    /**
     * Get the current sync status.
     *
     * @return array{
     *     status: string,
     *     total: int,
     *     done: int,
     *     errors: int,
     *     percentage: int,
     *     time: string,
     *     needs_sync: bool
     * }
     */
    public function get_status(): array {
        $status = $this->get_option( 'status', 'idle' );
        $total  = (int) $this->get_option( 'total', 0 );
        $done   = (int) $this->get_option( 'done', 0 );
        $errors = (int) $this->get_option( 'errors', 0 );
        $time   = $this->get_option( 'time', '' );

        $percentage = $total > 0 ? (int) round( ( $done + $errors ) / $total * 100 ) : 0;

        return [
            'status'      => $status,
            'total'       => $total,
            'done'        => $done,
            'errors'      => $errors,
            'percentage'  => min( $percentage, 100 ),
            'time'        => $time,
            'needs_sync'  => get_option( 'ramon_chatbot_needs_initial_sync', false ),
        ];
    }

    // ------------------------------------------------------------------
    // Helpers
    // ------------------------------------------------------------------

    /**
     * Set the activation flag.
     */
    private function flag_activation(): void {
        update_option( self::OPT_PREFIX . 'status', 'running' );
        update_option( self::OPT_PREFIX . 'total', 0 );
        update_option( self::OPT_PREFIX . 'done', 0 );
        update_option( self::OPT_PREFIX . 'errors', 0 );
        update_option( self::OPT_PREFIX . 'time', current_time( 'mysql' ) );
    }

    /**
     * Read an option by name.
     */
    private function get_option( string $key, string $default = '' ): string {
        return get_option( self::OPT_PREFIX . $key, $default );
    }

    /**
     * Write an option by name.
     */
    private function update_option( string $key, $value ): void {
        update_option( self::OPT_PREFIX . $key, $value );
    }

    /**
     * Extract product data from a WooCommerce product object.
     *
     * @param \WC_Product $product The product object.
     * @return array|null Flat array of product fields, or null on failure.
     */
    private function extract_product_data( \WC_Product $product ): ?array {
        $id = $product->get_id();

        $permalink = get_permalink( $id );

        $image_id  = $product->get_image_id();
        $image_url = '';
        if ( $image_id ) {
            $image_url = wp_get_attachment_url( $image_id );
        }

        $terms      = get_the_terms( $id, 'product_cat' );
        $categories = '';
        if ( $terms && ! is_wp_error( $terms ) ) {
            $categories = implode( ',', array_map( function ( $t ) {
                return $t->name;
            }, $terms ) );
        }

        return [
            'product_id'  => (string) $id,
            'sku'         => $product->get_sku() ?: '',
            'name'        => $product->get_name(),
            'description' => $product->get_description(),
            'categories'  => $categories,
            'price'       => (float) $product->get_price(),
            'stock'       => (int) $product->get_stock_quantity(),
            'url'         => $permalink ?: '',
            'image_url'   => $image_url,
            'status'      => $product->get_status(),
        ];
    }

    /**
     * Send a batch of changes to the backend API.
     *
     * @param array $changes List of change dicts.
     * @return array|WP_Error Response body on success, WP_Error on failure.
     */
    private function send_batch( array $changes ) {
        $api_url = rtrim( get_option( 'ramon_api_url', '' ), '/' );
        $token   = ramon_chatbot_generate_token( 3600 );

        if ( empty( $api_url ) || empty( $token ) ) {
            return new \WP_Error( 'config', 'API URL or token not configured' );
        }

        $endpoint = $api_url . '/api/sync/products';
        $body     = wp_json_encode( [ 'changes' => $changes ] );

        $response = wp_remote_post( $endpoint, [
            'headers' => [
                'Content-Type'  => 'application/json',
                'Authorization' => 'Bearer ' . $token,
            ],
            'body'    => $body,
            'timeout' => 30,
        ] );

        if ( is_wp_error( $response ) ) {
            return $response;
        }

        $code = wp_remote_retrieve_response_code( $response );
        if ( $code >= 200 && $code < 300 ) {
            return json_decode( wp_remote_retrieve_body( $response ), true );
        }

        $detail = wp_remote_retrieve_body( $response );
        return new \WP_Error( 'http', "HTTP {$code}: {$detail}" );
    }
}
