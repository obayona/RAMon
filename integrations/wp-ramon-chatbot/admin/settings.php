<?php
if (!defined('ABSPATH')) {
    exit;
}

function ramon_chatbot_register_settings() {
    register_setting('ramon_chatbot_options', 'ramon_app_key');
    register_setting('ramon_chatbot_options', 'ramon_api_url');
}
add_action('admin_init', 'ramon_chatbot_register_settings');

function ramon_chatbot_admin_menu() {
    add_options_page(
        'RAMon Chatbot',
        'RAMon Chatbot',
        'manage_options',
        'ramon-chatbot',
        'ramon_chatbot_settings_page'
    );
}
add_action('admin_menu', 'ramon_chatbot_admin_menu');

function ramon_chatbot_settings_page() {
    $app_key   = get_option('ramon_app_key', '');
    $api_url   = get_option('ramon_api_url', '');
    $configured = !empty($app_key) && !empty($api_url);

    $last_change    = get_option('ramon_sync_last_change', 'Never');
    $initial_sync   = RAMon_Initial_Sync::instance();
    $sync_status    = $initial_sync->get_status();

    // Handle retry action
    if (isset($_POST['ramon_retry_failed']) && check_admin_referer('ramon_retry_failed')) {
        $initial_sync->retry_failed();
        echo '<div class="notice notice-info"><p>Retrying failed products.</p></div>';
    }
    ?>
    <div class="wrap">
        <h1>RAMon Chatbot Settings</h1>

        <form method="post" action="options.php">
            <?php settings_fields('ramon_chatbot_options'); ?>
            <table class="form-table">
                <tr>
                    <th scope="row"><label for="ramon_app_key">App Key</label></th>
                    <td>
                        <input type="password"
                               id="ramon_app_key"
                               name="ramon_app_key"
                               value="<?php echo esc_attr($app_key); ?>"
                               class="regular-text"
                               autocomplete="off"
                               required />
                        <p class="description">The shared secret used to sign the JWT token. Must match the backend APP_KEY.</p>
                    </td>
                </tr>
                <tr>
                    <th scope="row"><label for="ramon_api_url">API URL</label></th>
                    <td>
                        <input type="url"
                               id="ramon_api_url"
                               name="ramon_api_url"
                               value="<?php echo esc_attr($api_url); ?>"
                               class="regular-text"
                               placeholder="https://example.com/api"
                               required />
                        <p class="description">The backend API URL for the chatbot.</p>
                    </td>
                </tr>
            </table>
            <?php submit_button('Save Settings'); ?>
        </form>

        <h2>Product Sync</h2>
        <table class="form-table">
            <tr>
                <th scope="row">Status</th>
                <td>
                    <?php if (!$configured) : ?>
                        <span style="color:orange;">Not configured</span> — Set the App Key and API URL above.
                    <?php elseif ($sync_status['status'] === 'running') : ?>
                        <span style="color:#0073aa;">Syncing</span> — Initial product sync is in progress.
                    <?php elseif ($sync_status['status'] === 'idle' && $sync_status['needs_sync']) : ?>
                        <span style="color:orange;">Pending</span> — Initial sync will start on next page load.
                    <?php else : ?>
                        <span style="color:green;">Active</span> — Product changes are sent to the backend automatically.
                    <?php endif; ?>
                </td>
            </tr>
            <tr>
                <th scope="row">Last Product Change</th>
                <td><?php echo esc_html($last_change); ?></td>
            </tr>
        </table>

        <?php if ($configured && $sync_status['status'] !== 'idle') : ?>
            <h2>Initial Sync Progress</h2>
            <table class="form-table">
                <tr>
                    <th scope="row">Progress</th>
                    <td>
                        <div style="background:#e0e0e0;border-radius:4px;height:24px;width:300px;position:relative;margin:4px 0;">
                            <div style="background:<?php echo $sync_status['status'] === 'complete' ? '#46b450' : '#0073aa'; ?>;height:100%;border-radius:4px;width:<?php echo esc_attr($sync_status['percentage']); ?>%;transition:width 0.3s;"></div>
                            <span style="position:absolute;top:2px;left:10px;font-size:13px;font-weight:bold;color:#333;">
                                <?php echo esc_html($sync_status['percentage']); ?>%
                            </span>
                        </div>
                    </td>
                </tr>
                <tr>
                    <th scope="row">Products</th>
                    <td>
                        <?php echo esc_html($sync_status['done']); ?> synced
                        <?php if ($sync_status['errors'] > 0) : ?>
                            · <span style="color:red;"><?php echo esc_html($sync_status['errors']); ?> failed</span>
                        <?php endif; ?>
                        of <?php echo esc_html($sync_status['total']); ?> total
                    </td>
                </tr>
                <tr>
                    <th scope="row">Last Updated</th>
                    <td><?php echo esc_html($sync_status['time'] ?: '—'); ?></td>
                </tr>
                <?php if ($sync_status['errors'] > 0 && $sync_status['status'] === 'complete') : ?>
                    <tr>
                        <th scope="row">Retry Failed</th>
                        <td>
                            <form method="post" style="display:inline;">
                                <?php wp_nonce_field('ramon_retry_failed'); ?>
                                <input type="hidden" name="ramon_retry_failed" value="1" />
                                <?php submit_button('Retry Failed Products', 'small', '', false); ?>
                            </form>
                        </td>
                    </tr>
                <?php endif; ?>
            </table>
        <?php endif; ?>

        <p class="description">
            Product changes are sent to the backend automatically when products
            are created, updated, or deleted. The backend processes them in the
            background via a worker that runs every minute.
        </p>
    </div>
    <?php
}
