<?php
/**
 * Product sync module for RAMon Chatbot.
 *
 * Handles real-time WooCommerce product change notifications.
 * Sends upsert/delete requests to the backend API whenever a product
 * is created, updated, or deleted in WordPress.
 *
 * Initial bulk sync is handled by RAMon_Initial_Sync in ramon-chatbot.php.
 */

if (!defined('ABSPATH')) {
    exit;
}

// ---------------------------------------------------------------------------
// WooCommerce product data extraction
// ---------------------------------------------------------------------------

/**
 * Extract WooCommerce product data into a flat array for sync.
 */
function ramon_chatbot_extract_product_data($product_id) {
    $product = wc_get_product($product_id);
    if (!$product) {
        return null;
    }

    $permalink = get_permalink($product_id);

    $image_id  = $product->get_image_id();
    $image_url = '';
    if ($image_id) {
        $image_url = wp_get_attachment_url($image_id);
    }

    $terms      = get_the_terms($product_id, 'product_cat');
    $categories = '';
    if ($terms && !is_wp_error($terms)) {
        $categories = implode(',', array_map(function ($t) {
            return $t->name;
        }, $terms));
    }

    return [
        'product_id'  => (string) $product_id,
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

// ---------------------------------------------------------------------------
// Send changes to backend
// ---------------------------------------------------------------------------

/**
 * Send a batch of product changes to the backend sync endpoint.
 *
 * @param array $changes List of change dicts with keys: action, product_id, fields.
 * @return array|WP_Error Response body on success, WP_Error on failure.
 */
function ramon_sync_send($changes) {
    $api_url = rtrim(get_option('ramon_api_url', ''), '/');
    $token   = ramon_chatbot_generate_token(3600);

    if (empty($api_url) || empty($token)) {
        return new WP_Error('config', 'API URL or token not configured');
    }

    $endpoint = $api_url . '/api/sync/products';
    $body     = wp_json_encode(['changes' => $changes]);

    $response = wp_remote_post($endpoint, [
        'headers' => [
            'Content-Type'  => 'application/json',
            'Authorization' => 'Bearer ' . $token,
        ],
        'body'    => $body,
        'timeout' => 15,
    ]);

    if (is_wp_error($response)) {
        return $response;
    }

    $code = wp_remote_retrieve_response_code($response);
    if ($code >= 200 && $code < 300) {
        return json_decode(wp_remote_retrieve_body($response), true);
    }

    $detail = wp_remote_retrieve_body($response);
    return new WP_Error('http', "HTTP $code: $detail");
}

// ---------------------------------------------------------------------------
// WooCommerce hook handlers
// ---------------------------------------------------------------------------

/**
 * Send an upsert when a product is created or updated.
 */
function ramon_chatbot_on_product_change($product_id, $product = null) {
    if (get_post_type($product_id) !== 'product') {
        return;
    }

    $data = ramon_chatbot_extract_product_data($product_id);
    if (!$data) {
        return;
    }

    ramon_sync_send([[
        'action'     => 'upsert',
        'product_id' => $data['product_id'],
        'fields'     => $data,
    ]]);

    update_option('ramon_sync_last_change', current_time('mysql'));
}

add_action('woocommerce_update_product', 'ramon_chatbot_on_product_change', 10, 2);
add_action('woocommerce_new_product',    'ramon_chatbot_on_product_change', 10, 2);

/**
 * Send a delete when a product is about to be removed.
 */
function ramon_chatbot_on_product_delete($product_id) {
    if (get_post_type($product_id) !== 'product') {
        return;
    }

    ramon_sync_send([[
        'action'     => 'delete',
        'product_id' => (string) $product_id,
        'fields'     => [],
    ]]);

    update_option('ramon_sync_last_change', current_time('mysql'));
}

add_action('before_delete_post', 'ramon_chatbot_on_product_delete');
