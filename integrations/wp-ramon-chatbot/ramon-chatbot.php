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
define('RAMON_CHATBOT_PLUGIN_FILE', __FILE__);

require_once __DIR__ . '/vendor/autoload.php';

$plugin = new \Ramon\Chatbot\Plugin();
$plugin->boot(RAMON_CHATBOT_PLUGIN_DIR, RAMON_CHATBOT_PLUGIN_URL);
