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

require_once RAMON_CHATBOT_PLUGIN_DIR . 'admin/settings.php';

/**
 * Generate a JWT token signed with the app_key (HMAC-SHA256).
 */
function ramon_chatbot_generate_token() {
    $app_key = get_option('ramon_app_key', '');
    if (empty($app_key)) {
        return '';
    }

    $header = ramon_chatbot_base64url_encode(json_encode(['alg' => 'HS256', 'typ' => 'JWT']));
    $payload = ramon_chatbot_base64url_encode(json_encode(['iat' => time()]));
    $signature = ramon_chatbot_base64url_encode(
        hash_hmac('sha256', "$header.$payload", $app_key, true)
    );

    return "$header.$payload.$signature";
}

function ramon_chatbot_base64url_encode($data) {
    return rtrim(strtr(base64_encode($data), '+/', '-_'), '=');
}

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

/**
 * Enqueue the chatbot widget on the frontend.
 * Follows the same logic as startProd() in frontend/server.cjs:
 * - Injects __RAMON_CONFIG__ with token, apiUrl, assetsUrl, and optionally productId
 * - Loads ramon.js from the plugin's assets folder
 * - ramon.js uses assetsUrl to dynamically load ramon-burble.js
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
