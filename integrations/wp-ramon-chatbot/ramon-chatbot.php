<?php
/**
 * Plugin Name: RAMon Chatbot
 * Description: Injects the RAMon AI chatbot bubble into your WordPress site.
 * Version: 1.0.0
 * Author: RAMon
 * License: MIT
 * Text Domain: ramon-chatbot
 */

if (!defined('ABSPATH')) {
    exit;
}

define('RAMON_CHATBOT_VERSION', '1.0.0');
define('RAMON_CHATBOT_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('RAMON_CHATBOT_PLUGIN_URL', plugin_dir_url(__FILE__));

require_once RAMON_CHATBOT_PLUGIN_DIR . 'includes/jwt.php';
require_once RAMON_CHATBOT_PLUGIN_DIR . 'includes/class-ramon-initial-sync.php';
require_once RAMON_CHATBOT_PLUGIN_DIR . 'admin/settings.php';
require_once RAMON_CHATBOT_PLUGIN_DIR . 'sync.php';

// ---------------------------------------------------------------------------
// Plugin lifecycle hooks
// ---------------------------------------------------------------------------

$ramon_initial_sync = RAMon_Initial_Sync::instance();

register_activation_hook(__FILE__, [ $ramon_initial_sync, 'on_activate' ]);
register_deactivation_hook(__FILE__, [ $ramon_initial_sync, 'on_deactivate' ]);

// Cron callback
add_action(RAMon_Initial_Sync::CRON_HOOK, [ $ramon_initial_sync, 'process_cron' ]);

// Drop sync table after finalization
add_action('admin_init', [ $ramon_initial_sync, 'maybe_drop_table' ]);

// Register the one-minute cron interval
add_filter('cron_schedules', function (array $schedules): array {
    $schedules['one_minute'] = [
        'interval' => 60,
        'display'  => __('Every Minute', 'ramon-chatbot'),
    ];
    return $schedules;
});

// ---------------------------------------------------------------------------
// Frontend helpers
// ---------------------------------------------------------------------------

/**
 * Check if the current page is a WooCommerce product page.
 */
function ramon_chatbot_is_product_page() {
    return function_exists('is_product') && is_product();
}

/**
 * Get the post ID for the current WooCommerce product page.
 */
function ramon_chatbot_get_product_id() {
    global $post;
    if (ramon_chatbot_is_product_page() && $post) {
        return $post->ID;
    }
    return null;
}

// ---------------------------------------------------------------------------
// Enqueue chatbot widget
// ---------------------------------------------------------------------------

/**
 * Enqueue the chatbot widget on the frontend.
 * Injects __RAMON_CONFIG__ with token, apiUrl, assetsUrl, and optionally productId,
 * then loads ramon.js which bootstraps ramon-burble.js.
 */
function ramon_chatbot_enqueue() {
    $app_key = get_option('ramon_app_key', '');
    $api_url = get_option('ramon_api_url', '');

    if (empty($app_key) || empty($api_url)) {
        return;
    }

    $token = ramon_chatbot_generate_token();
    $assets_url = RAMON_CHATBOT_PLUGIN_URL . 'assets';
    $product_id = ramon_chatbot_get_product_id();

    $config = [
        'token'     => $token,
        'apiUrl'    => $api_url,
        'assetsUrl' => $assets_url,
    ];

    if ($product_id) {
        $config['productId'] = (string) $product_id;
    }

    $config_json = wp_json_encode($config);

    echo "<script>window.__RAMON_CONFIG__ = $config_json;</script>\n";
    echo '<script src="' . esc_url(RAMON_CHATBOT_PLUGIN_URL . 'assets/ramon.js') . '"></script>' . "\n";
}
add_action('wp_footer', 'ramon_chatbot_enqueue');
