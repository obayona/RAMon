<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Admin;

use Ramon\Chatbot\Domain\SyncStatus;
use Ramon\Chatbot\Ports\OptionStore;
use Ramon\Chatbot\Sync\InitialSync;

/**
 * Admin sync page for RAMon Chatbot.
 *
 * Renders sync status, progress UI, and force sync / retry actions.
 */
final class SyncPage
{
    public function __construct(
        private readonly OptionStore $options,
        private readonly InitialSync $initialSync,
    ) {
    }

    /**
     * Render the sync page.
     */
    public function renderPage(): void
    {
        $this->handleForceSyncAction();
        $this->handleRetryAction();

        $appKey = (string) $this->options->get('ramon_app_key', '');
        $apiUrl = (string) $this->options->get('ramon_api_url', '');
        $configured = $appKey !== '' && $apiUrl !== '';
        $lastChange = (string) $this->options->get('ramon_sync_last_change', 'Never');
        $syncStatus = $this->initialSync->getStatus();

        ?>
        <div class="wrap">
            <h1>RAMon Chatbot — Sync</h1>

            <h2>Product Sync</h2>
            <table class="form-table">
                <tr>
                    <th scope="row">Status</th>
                    <td><?php $this->renderStatus($configured, $syncStatus); ?></td>
                </tr>
                <tr>
                    <th scope="row">Last Product Change</th>
                    <td><?php echo \esc_html($lastChange); ?></td>
                </tr>
            </table>

            <?php if ($configured && $syncStatus->status !== SyncStatus::STATUS_IDLE) : ?>
                <?php $this->renderSyncProgress($syncStatus); ?>
            <?php endif; ?>

            <p class="description">
                Product changes are sent to the backend automatically when products
                are created, updated, or deleted. The backend processes them in the
                background via a worker that runs every minute.
            </p>

            <?php if ($configured && $syncStatus->status !== SyncStatus::STATUS_RUNNING) : ?>
                <form method="post" style="margin-top:16px;">
                    <?php \wp_nonce_field('ramon_force_sync'); ?>
                    <input type="hidden" name="ramon_force_sync" value="1" />
                    <button type="submit" class="button button-secondary" onclick="return confirm('This will re-sync all products from scratch. Continue?');">
                        Force Sync
                    </button>
                    <p class="description" style="margin-left:8px;display:inline;">
                        Drop and restart the initial product sync for all products.
                    </p>
                </form>
            <?php endif; ?>
        </div>
        <?php
    }

    // ------------------------------------------------------------------
    // Private helpers
    // ------------------------------------------------------------------

    /**
     * Handle the force sync action if submitted.
     */
    private function handleForceSyncAction(): void
    {
        if (isset($_POST['ramon_force_sync']) && \check_admin_referer('ramon_force_sync')) {
            $this->initialSync->startSync();
            echo '<div class="notice notice-info"><p>Initial product sync has been restarted.</p></div>';
        }
    }

    /**
     * Handle the retry action if submitted.
     */
    private function handleRetryAction(): void
    {
        if (isset($_POST['ramon_retry_failed']) && \check_admin_referer('ramon_retry_failed')) {
            $this->initialSync->retryFailed();
            echo '<div class="notice notice-info"><p>Retrying failed products.</p></div>';
        }
    }

    /**
     * Render the status line.
     */
    private function renderStatus(bool $configured, SyncStatus $status): void
    {
        if (!$configured) {
            echo '<span style="color:orange;">Not configured</span> — Set the App Key and API URL on the <a href="' . \esc_url(\admin_url('admin.php?page=ramon-chatbot')) . '">Settings page</a>.';
            return;
        }

        if ($status->status === SyncStatus::STATUS_RUNNING) {
            echo '<span style="color:#0073aa;">Syncing</span> — Initial product sync is in progress.';
            return;
        }

        if ($status->status === SyncStatus::STATUS_IDLE && $status->needsSync) {
            echo '<span style="color:orange;">Pending</span> — Initial sync will start on next page load.';
            return;
        }

        echo '<span style="color:green;">Active</span> — Product changes are sent to the backend automatically.';
    }

    /**
     * Render the initial sync progress section.
     */
    private function renderSyncProgress(SyncStatus $status): void
    {
        $barColor = $status->status === SyncStatus::STATUS_COMPLETE ? '#46b450' : '#0073aa';
        ?>
        <h2>Initial Sync Progress</h2>
        <table class="form-table">
            <tr>
                <th scope="row">Progress</th>
                <td>
                    <div style="background:#e0e0e0;border-radius:4px;height:24px;width:300px;position:relative;margin:4px 0;">
                        <div style="background:<?php echo $barColor; ?>;height:100%;border-radius:4px;width:<?php echo \esc_attr($status->percentage); ?>%;transition:width 0.3s;"></div>
                        <span style="position:absolute;top:2px;left:10px;font-size:13px;font-weight:bold;color:#333;">
                            <?php echo \esc_html((string) $status->percentage); ?>%
                        </span>
                    </div>
                </td>
            </tr>
            <tr>
                <th scope="row">Products</th>
                <td>
                    <?php echo \esc_html((string) $status->done); ?> synced
                    <?php if ($status->errors > 0) : ?>
                        · <span style="color:red;"><?php echo \esc_html((string) $status->errors); ?> failed</span>
                    <?php endif; ?>
                    of <?php echo \esc_html((string) $status->total); ?> total
                </td>
            </tr>
            <tr>
                <th scope="row">Last Updated</th>
                <td><?php echo \esc_html($status->time ?: '—'); ?></td>
            </tr>
            <?php if ($status->errors > 0 && $status->status === SyncStatus::STATUS_COMPLETE) : ?>
                <tr>
                    <th scope="row">Retry Failed</th>
                    <td>
                        <form method="post" style="display:inline;">
                            <?php \wp_nonce_field('ramon_retry_failed'); ?>
                            <input type="hidden" name="ramon_retry_failed" value="1" />
                            <?php \submit_button('Retry Failed Products', 'small', '', false); ?>
                        </form>
                    </td>
                </tr>
            <?php endif; ?>
        </table>
        <?php
    }
}
