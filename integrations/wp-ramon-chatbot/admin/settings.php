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
                               value="<?php echo esc_attr(get_option('ramon_app_key', '')); ?>"
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
                               value="<?php echo esc_attr(get_option('ramon_api_url', '')); ?>"
                               class="regular-text"
                               placeholder="https://example.com/api"
                               required />
                        <p class="description">The backend API URL for the chatbot.</p>
                    </td>
                </tr>
            </table>
            <?php submit_button('Save Settings'); ?>
        </form>
    </div>
    <?php
}
