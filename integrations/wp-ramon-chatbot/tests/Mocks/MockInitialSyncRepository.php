<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Tests\Mocks;

use Ramon\Chatbot\Ports\InitialSyncRepository;

/**
 * In-memory mock for InitialSyncRepository.
 *
 * Stores product IDs in a PHP array to simulate the sync table.
 */
final class MockInitialSyncRepository implements InitialSyncRepository
{
    private bool $tableExists = false;

    /** @var list<array{id: int, product_id: int, status: string, error: ?string}> */
    private array $rows = [];

    private int $nextId = 1;

    public function setTableExists(bool $exists): void
    {
        $this->tableExists = $exists;
    }

    public function tableExists(): bool
    {
        return $this->tableExists;
    }

    public function createTable(): void
    {
        $this->tableExists = true;
    }

    public function dropTable(): void
    {
        $this->tableExists = false;
        $this->rows = [];
    }

    public function insertProductIds(array $productIds): void
    {
        foreach ($productIds as $pid) {
            $this->rows[] = [
                'id' => $this->nextId++,
                'product_id' => $pid,
                'status' => 'pending',
                'error' => null,
            ];
        }
    }

    public function fetchPendingBatch(int $limit): array
    {
        $result = [];
        foreach ($this->rows as $row) {
            if ($row['status'] === 'pending') {
                $result[] = $row['product_id'];
                if (\count($result) >= $limit) {
                    break;
                }
            }
        }
        return $result;
    }

    public function countPending(): int
    {
        $count = 0;
        foreach ($this->rows as $row) {
            if ($row['status'] === 'pending') {
                $count++;
            }
        }
        return $count;
    }

    public function markStatus(array $ids, string $status, string $error = ''): void
    {
        $idSet = \array_flip(\array_map('strval', $ids));
        foreach ($this->rows as &$row) {
            if (isset($idSet[(string) $row['product_id']])) {
                $row['status'] = $status;
                $row['error'] = $error !== '' ? $error : null;
            }
        }
    }

    public function retryFailed(): int
    {
        $count = 0;
        foreach ($this->rows as &$row) {
            if ($row['status'] === 'error') {
                $row['status'] = 'pending';
                $row['error'] = null;
                $count++;
            }
        }
        return $count;
    }

    /**
     * Get all rows for assertions.
     *
     * @return list<array{id: int, product_id: int, status: string, error: ?string}>
     */
    public function getRows(): array
    {
        return $this->rows;
    }
}
