<?php
/**
 * Shared JWT helpers for RAMon Chatbot.
 *
 * Used by both the frontend widget and the sync module.
 */

if (!defined('ABSPATH')) {
    exit;
}

/**
 * Base64url-encode raw data (RFC 7515 §2).
 */
function ramon_chatbot_base64url_encode($data) {
    return rtrim(strtr(base64_encode($data), '+/', '-_'), '=');
}

/**
 * Generate a JWT token signed with the app_key (HMAC-SHA256).
 *
 * @param int $expires_in Seconds until the token expires.
 *                        0 = no expiry (default, for the widget).
 *                        3600 = 1 hour (for sync requests).
 * @return string The encoded JWT string, or empty string on missing key.
 */
function ramon_chatbot_generate_token($expires_in = 0) {
    $app_key = get_option('ramon_app_key', '');
    if (empty($app_key)) {
        return '';
    }

    $claims = ['iat' => time()];
    if ($expires_in > 0) {
        $claims['exp'] = time() + $expires_in;
    }

    $header    = ramon_chatbot_base64url_encode(json_encode(['alg' => 'HS256', 'typ' => 'JWT']));
    $payload   = ramon_chatbot_base64url_encode(json_encode($claims));
    $signature = ramon_chatbot_base64url_encode(
        hash_hmac('sha256', "$header.$payload", $app_key, true)
    );

    return "$header.$payload.$signature";
}
