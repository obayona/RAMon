<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Sync;

use Ramon\Chatbot\Ports\Clock;
use Ramon\Chatbot\Ports\CronScheduler;
use Ramon\Chatbot\Ports\InitialSyncRepository;
use Ramon\Chatbot\Ports\OptionStore;
use Ramon\Chatbot\Ports\ProductExtractor;
use Ramon\Chatbot\Ports\ProductQuery;
use Ramon\Chatbot\Ports\SiteIterator;
use Ramon\Chatbot\Ports\TransientStore;
use Ramon\Chatbot\Services\SyncService;

/**
 * Initial bulk product sync on plugin activation.
 *
 * Populates a temporary table with published product IDs, then processes
 * them in batches via WP-Cron. The table is dropped once complete.
 */
final class InitialSync
{
    private const CRON_HOOK = 'ramon_initial_sync_hook';
    private const OPT_PREFIX = 'ramon_initial_sync_';
    private const TABLE_DROP_TRANSIENT = 'ramon_drop_initial_sync_table';

    public function __construct(
        private readonly OptionStore $options,
        private readonly Clock $clock,
        private readonly SyncService $sync,
        private readonly ProductExtractor $extractor,
        private readonly InitialSyncRepository $repo,
        private readonly CronScheduler $cron,
        private readonly ProductQuery $productQuery,
        private readonly TransientStore $transients,
        private readonly SiteIterator $sites,
        private readonly int $batchSize = 100,
    ) {
    }

    /**
     * Get the WP-Cron hook name for external registration.
     */
    public static function cronHook(): string
    {
        return self::CRON_HOOK;
    }

    // ------------------------------------------------------------------
    // Activation / Deactivation
    // ------------------------------------------------------------------

    /**
     * Handle plugin activation — set a flag, no heavy work.
     */
    public function onActivate(bool $networkWide): void
    {
        if ($networkWide) {
            $this->sites->forEachSite(fn () => $this->flagActivation());
        } else {
            $this->flagActivation();
        }
    }

    /**
     * Handle plugin deactivation — clean up cron and options.
     */
    public function onDeactivate(): void
    {
        $this->unscheduleCron();
        $this->options->delete(self::OPT_PREFIX . 'locked');
    }

    // ------------------------------------------------------------------
    // Cron
    // ------------------------------------------------------------------

    /**
     * Schedule the cron event if not already scheduled.
     */
    public function scheduleCron(): void
    {
        if (!$this->cron->isScheduled(self::CRON_HOOK)) {
            $this->cron->schedule(self::CRON_HOOK, $this->clock->now(), 'one_minute');
        }
    }

    /**
     * Unschedule the cron event.
     */
    public function unscheduleCron(): void
    {
        $timestamp = $this->cron->getNextTimestamp(self::CRON_HOOK);
        if ($timestamp !== false) {
            $this->cron->unschedule($timestamp, self::CRON_HOOK);
        }
    }

    /**
     * Main cron callback — orchestrates the entire initial sync.
     */
    public function processCron(): void
    {
        if ($this->opt('status') !== 'running') {
            return;
        }

        if ($this->options->get(self::OPT_PREFIX . 'locked', false)) {
            return;
        }
        $this->options->set(self::OPT_PREFIX . 'locked', true);

        try {
            if (!$this->repo->tableExists()) {
                $this->createAndPopulateTable();
            }

            $result = $this->processBatch();

            if ($result['pending'] === 0) {
                $this->finalize();
            }
        } finally {
            $this->options->delete(self::OPT_PREFIX . 'locked');
        }
    }

    // ------------------------------------------------------------------
    // Table lifecycle
    // ------------------------------------------------------------------

    /**
     * Create the sync table and populate it with product IDs.
     */
    private function createAndPopulateTable(): void
    {
        $this->repo->createTable();

        $total = $this->productQuery->countPublished();
        $pages = (int) \ceil($total / 100);

        $this->setOpt('total', $total);
        $this->setOpt('done', 0);
        $this->setOpt('errors', 0);
        $this->setOpt('time', $this->clock->mysql());

        for ($p = 1; $p <= $pages; $p++) {
            $ids = $this->productQuery->fetchProductIds($p, 100);
            $this->repo->insertProductIds($ids);
        }
    }

    // ------------------------------------------------------------------
    // Batch processing
    // ------------------------------------------------------------------

    /**
     * Process one batch of pending products.
     *
     * @return array{pending: int, processed: int, errors: int}
     */
    private function processBatch(): array
    {
        $productIds = $this->repo->fetchPendingBatch($this->batchSize);

        if (empty($productIds)) {
            return ['pending' => 0, 'processed' => 0, 'errors' => 0];
        }

        $changes = [];
        foreach ($productIds as $pid) {
            $data = $this->extractor->extract($pid);
            if ($data !== null) {
                $changes[] = [
                    'action' => 'upsert',
                    'product_id' => $data->productId,
                    'fields' => $data->toArray(),
                ];
            }
        }

        $processed = 0;
        $errors = 0;

        if (!empty($changes)) {
            $result = $this->sync->send($changes);

            if (!$result['success']) {
                $this->repo->markStatus($productIds, 'error', $result['error'] ?? 'Unknown error');
                $errors = \count($productIds);
            } else {
                $this->repo->markStatus($productIds, 'done');
                $processed = \count($productIds);
            }
        }

        $pending = $this->repo->countPending();

        $doneTotal = (int) $this->opt('done', '0') + $processed;
        $errorTotal = (int) $this->opt('errors', '0') + $errors;

        $this->setOpt('done', $doneTotal);
        $this->setOpt('errors', $errorTotal);
        $this->setOpt('time', $this->clock->mysql());

        return [
            'pending' => $pending,
            'processed' => $processed,
            'errors' => $errors,
        ];
    }

    // ------------------------------------------------------------------
    // Finalization
    // ------------------------------------------------------------------

    /**
     * Mark sync as complete, unschedule cron, schedule table drop.
     */
    private function finalize(): void
    {
        $this->setOpt('status', 'complete');
        $this->setOpt('time', $this->clock->mysql());
        $this->unscheduleCron();
        $this->transients->set(self::TABLE_DROP_TRANSIENT, true, 60);
    }

    /**
     * Drop the sync table if flagged for cleanup. Hooked to admin_init.
     */
    public function maybeDropTable(): void
    {
        if ($this->transients->get(self::TABLE_DROP_TRANSIENT)) {
            $this->transients->delete(self::TABLE_DROP_TRANSIENT);
            if ($this->repo->tableExists()) {
                $this->repo->dropTable();
            }
        }
    }

    // ------------------------------------------------------------------
    // Retry
    // ------------------------------------------------------------------

    /**
     * Reset all error rows back to pending.
     *
     * @return int Number of rows reset.
     */
    public function retryFailed(): int
    {
        $count = $this->repo->retryFailed();

        if ($count) {
            $this->setOpt('errors', 0);
            $this->setOpt('time', $this->clock->mysql());
            $this->setOpt('status', 'running');
            $this->scheduleCron();
        }

        return $count;
    }

    // ------------------------------------------------------------------
    // Status (for admin UI)
    // ------------------------------------------------------------------

    /**
     * Get the current sync status.
     */
    public function getStatus(): \Ramon\Chatbot\Domain\SyncStatus
    {
        return \Ramon\Chatbot\Domain\SyncStatus::fromOptions(
            status: $this->opt('status', 'idle'),
            total: (int) $this->opt('total', '0'),
            done: (int) $this->opt('done', '0'),
            errors: (int) $this->opt('errors', '0'),
            time: $this->opt('time', ''),
            needsSync: (bool) $this->options->get('ramon_chatbot_needs_initial_sync', false),
        );
    }

    // ------------------------------------------------------------------
    // Helpers
    // ------------------------------------------------------------------

    private function flagActivation(): void
    {
        $this->setOpt('status', 'running');
        $this->setOpt('total', 0);
        $this->setOpt('done', 0);
        $this->setOpt('errors', 0);
        $this->setOpt('time', $this->clock->mysql());
    }

    private function opt(string $key, string $default = ''): string
    {
        return (string) $this->options->get(self::OPT_PREFIX . $key, $default);
    }

    private function setOpt(string $key, mixed $value): void
    {
        $this->options->set(self::OPT_PREFIX . $key, $value);
    }
}
