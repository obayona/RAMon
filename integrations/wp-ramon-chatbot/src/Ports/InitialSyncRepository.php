<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Ports;

/**
 * Abstraction for the initial sync queue table.
 *
 * All raw SQL on the sync table goes through this interface,
 * making the orchestration logic testable without a database.
 */
interface InitialSyncRepository
{
    /**
     * Check if the sync queue table exists.
     */
    public function tableExists(): bool;

    /**
     * Create the sync queue table.
     */
    public function createTable(): void;

    /**
     * Drop the sync queue table.
     */
    public function dropTable(): void;

    /**
     * Insert a batch of product IDs into the queue as pending.
     *
     * @param int[] $productIds
     */
    public function insertProductIds(array $productIds): void;

    /**
     * Fetch the next batch of pending product IDs.
     *
     * @return int[] Product IDs ordered by insertion order.
     */
    public function fetchPendingBatch(int $limit): array;

    /**
     * Count remaining pending rows.
     */
    public function countPending(): int;

    /**
     * Mark product IDs with a given status.
     *
     * @param int[]  $ids
     * @param string $status
     * @param string $error
     */
    public function markStatus(array $ids, string $status, string $error = ''): void;

    /**
     * Reset all error rows back to pending.
     *
     * @return int Number of rows reset.
     */
    public function retryFailed(): int;
}
