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
    private const NEEDS_SYNC_KEY = 'ramon_chatbot_needs_initial_sync';

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
     * Handle plugin activation — set a flag, schedule cron.
     */
    public function onActivate(bool $networkWide): void
    {
        $this->log('Plugin activation started (networkWide=' . ($networkWide ? 'true' : 'false') . ')');

        if (\defined('DISABLE_WP_CRON') && \DISABLE_WP_CRON) {
            $this->log('WARNING: DISABLE_WP_CRON is true — WP-Cron is disabled. The admin fallback will handle sync.');
        }

        if ($networkWide) {
            $this->sites->forEachSite(fn () => $this->flagActivation());
        } else {
            $this->flagActivation();
        }

        $this->log('Plugin activation complete — cron scheduled. Note: WP-Cron fires on page loads. Visit any page to trigger sync.');
    }

    /**
     * Handle plugin deactivation — clean up cron and options.
     */
    public function onDeactivate(): void
    {
        $this->log('Plugin deactivation — cleaning up');
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
            $this->log('Cron scheduled');
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
            $this->log('Cron unscheduled');
        }
    }

    /**
     * Main cron callback — orchestrates the entire initial sync.
     */
    public function processCron(): void
    {
        $status = $this->opt('status');
        $this->log("processCron triggered — status={$status}");

        if ($status !== 'running') {
            $this->log('processCron: status is not running, skipping');
            return;
        }

        if ($this->options->get(self::OPT_PREFIX . 'locked', false)) {
            $this->log('processCron: locked by another process, skipping');
            return;
        }
        $this->options->set(self::OPT_PREFIX . 'locked', true);

        try {
            if (!$this->repo->tableExists()) {
                $this->log('processCron: creating and populating sync table');
                $this->createAndPopulateTable();
            }

            $result = $this->processBatch();
            $this->log("processCron: batch done — processed={$result['processed']}, errors={$result['errors']}, pending={$result['pending']}");

            if ($result['pending'] === 0) {
                $this->finalize($result['errors'] > 0);
            }
        } catch (\Throwable $e) {
            $this->log('processCron: exception — ' . $e->getMessage());
            throw $e;
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

        $this->log("createAndPopulateTable: total={$total}, pages={$pages}");

        for ($p = 1; $p <= $pages; $p++) {
            $ids = $this->productQuery->fetchProductIds($p, 100);
            $this->repo->insertProductIds($ids);
        }

        $this->log('createAndPopulateTable: table populated');
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

        $this->log('processBatch: processing ' . \count($productIds) . ' products — IDs: ' . implode(', ', $productIds));

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
            $this->log('processBatch: sending ' . \count($changes) . ' changes to backend');
            $result = $this->sync->send($changes);

            if (!$result['success']) {
                $error = $result['error'] ?? 'Unknown error';
                $this->log('processBatch: backend error — ' . $error);
                $this->repo->markStatus($productIds, 'error', $error);
                $errors = \count($productIds);
            } else {
                $this->repo->markStatus($productIds, 'done');
                $processed = \count($productIds);
            }
        } else {
            $this->log('processBatch: no extractable products in batch');
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
     * Mark sync as complete, unschedule cron, optionally schedule table drop.
     *
     * The table is only dropped when there are no errors, so retry can use it.
     */
    private function finalize(bool $hasErrors = false): void
    {
        $done = (int) $this->opt('done', '0');
        $errors = (int) $this->opt('errors', '0');
        $this->log("finalize: sync complete — done={$done}, errors={$errors}");

        $this->setOpt('status', 'complete');
        $this->setOpt('time', $this->clock->mysql());
        $this->options->delete(self::NEEDS_SYNC_KEY);
        $this->unscheduleCron();

        if (!$hasErrors) {
            $this->transients->set(self::TABLE_DROP_TRANSIENT, true, 60);
        }
    }

    /**
     * Drop the sync table if flagged for cleanup. Hooked to admin_init.
     */
    public function maybeDropTable(): void
    {
        if ($this->transients->get(self::TABLE_DROP_TRANSIENT)) {
            $this->transients->delete(self::TABLE_DROP_TRANSIENT);
            if ($this->repo->tableExists()) {
                $this->log('maybeDropTable: dropping sync table');
                $this->repo->dropTable();
            }
        }
    }

    // ------------------------------------------------------------------
    // Force sync
    // ------------------------------------------------------------------

    /**
     * Force-start the initial sync from scratch.
     *
     * Drops any existing sync table and restarts the process.
     * Called from the admin "Force Sync" button.
     */
    public function startSync(): void
    {
        $this->log('startSync: force-starting initial sync');

        if ($this->repo->tableExists()) {
            $this->repo->dropTable();
        }

        $this->flagActivation();
    }

    // ------------------------------------------------------------------
    // Retry
    // ------------------------------------------------------------------

    /**
     * Drop the sync table and restart from scratch.
     *
     * The table will be recreated and repopulated on the next processCron run.
     *
     * @return int Number of error rows that existed before restart.
     */
    public function retryFailed(): int
    {
        $count = $this->repo->retryFailed();

        if ($count) {
            $this->log("retryFailed: restarting sync from scratch ({$count} errors)");
            $this->repo->dropTable();
            $this->setOpt('errors', 0);
            $this->setOpt('time', $this->clock->mysql());
            $this->setOpt('status', 'running');
            $this->scheduleCron();
        }

        return $count;
    }

    // ------------------------------------------------------------------
    // Admin fallback (WP-Cron backup)
    // ------------------------------------------------------------------

    /**
     * Trigger a sync batch on admin page loads when status is running.
     *
     * This is a fallback for environments where WP-Cron is disabled or
     * unreliable. Hooked to admin_init alongside the cron hook.
     */
    public function maybeProcessSync(): void
    {
        if ($this->opt('status') !== 'running') {
            return;
        }

        $this->log('admin_init fallback: sync is running, triggering batch');
        $this->processCron();
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
            needsSync: (bool) $this->options->get(self::NEEDS_SYNC_KEY, false),
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
        $this->options->set(self::NEEDS_SYNC_KEY, true);
        $this->scheduleCron();
    }

    private function opt(string $key, string $default = ''): string
    {
        return (string) $this->options->get(self::OPT_PREFIX . $key, $default);
    }

    private function setOpt(string $key, mixed $value): void
    {
        $this->options->set(self::OPT_PREFIX . $key, $value);
    }

    /**
     * Log a message to the PHP error log.
     */
    private function log(string $message): void
    {
        \error_log("[RAMon InitialSync] {$message}");
    }
}
