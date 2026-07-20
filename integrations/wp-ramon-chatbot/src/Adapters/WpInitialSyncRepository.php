<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Adapters;

use Ramon\Chatbot\Ports\InitialSyncRepository;

/**
 * WordPress/$wpdb implementation of InitialSyncRepository.
 */
final class WpInitialSyncRepository implements InitialSyncRepository
{
    private string $table;

    public function __construct()
    {
        global $wpdb;
        $this->table = $wpdb->prefix . 'ramon_initial_sync';
    }

    public function tableExists(): bool
    {
        global $wpdb;
        $escaped = \esc_sql($this->table);
        $result = $wpdb->get_var(
            "SELECT TABLE_NAME FROM information_schema.TABLES
             WHERE TABLE_SCHEMA = '{$wpdb->dbname}' AND TABLE_NAME = '{$escaped}'",
        );
        return $result !== null;
    }

    public function createTable(): void
    {
        global $wpdb;
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
    }

    public function dropTable(): void
    {
        global $wpdb;
        $wpdb->query("DROP TABLE IF EXISTS {$this->table}");
    }

    public function insertProductIds(array $productIds): void
    {
        global $wpdb;
        foreach ($productIds as $pid) {
            $wpdb->insert($this->table, [
                'product_id' => $pid,
                'status' => 'pending',
            ], ['%d', '%s']);
        }
    }

    public function fetchPendingBatch(int $limit): array
    {
        global $wpdb;
        return (array) $wpdb->get_col(
            $wpdb->prepare(
                "SELECT product_id FROM {$this->table}
                 WHERE status = 'pending'
                 ORDER BY id ASC
                 LIMIT %d",
                $limit,
            ),
        );
    }

    public function countPending(): int
    {
        global $wpdb;
        return (int) $wpdb->get_var(
            "SELECT COUNT(*) FROM {$this->table} WHERE status = 'pending'",
        );
    }

    public function markStatus(array $ids, string $status, string $error = ''): void
    {
        global $wpdb;

        if (empty($ids)) {
            return;
        }

        $placeholders = \implode(',', \array_fill(0, \count($ids), '%d'));

        if ($error !== '') {
            $wpdb->query($wpdb->prepare(
                "UPDATE {$this->table} SET status = %s, error = %s WHERE product_id IN ({$placeholders})",
                \array_merge([$status, $error], $ids),
            ));
        } else {
            $wpdb->query($wpdb->prepare(
                "UPDATE {$this->table} SET status = %s WHERE product_id IN ({$placeholders})",
                \array_merge([$status], $ids),
            ));
        }
    }

    public function retryFailed(): int
    {
        global $wpdb;
        return (int) $wpdb->query(
            "UPDATE {$this->table} SET status = 'pending', error = NULL WHERE status = 'error'",
        );
    }
}
