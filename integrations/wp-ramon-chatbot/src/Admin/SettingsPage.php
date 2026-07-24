<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Admin;

use Ramon\Chatbot\Ports\OptionStore;

/**
 * Admin settings page for RAMon Chatbot.
 *
 * Renders the settings form for App Key and API URL.
 */
final class SettingsPage
{
    public function __construct(
        private readonly OptionStore $options,
    ) {
    }

    /**
     * Register settings with WordPress.
     */
    public function register(): void
    {
        \add_action('admin_init', [$this, 'registerSettings']);
    }

    /**
     * Register settings with WordPress.
     */
    public function registerSettings(): void
    {
        \register_setting('ramon_chatbot_options', 'ramon_app_key');
        \register_setting('ramon_chatbot_options', 'ramon_api_url');
    }

    /**
     * Render the settings page.
     */
    public function renderPage(): void
    {
        $appKey = (string) $this->options->get('ramon_app_key', '');
        $apiUrl = (string) $this->options->get('ramon_api_url', '');

        ?>
        <div class="wrap">
            <h1>RAMon Chatbot — Settings</h1>

            <form method="post" action="options.php">
                <?php \settings_fields('ramon_chatbot_options'); ?>
                <table class="form-table">
                    <tr>
                        <th scope="row"><label for="ramon_app_key">App Key</label></th>
                        <td>
                            <input type="password"
                                   id="ramon_app_key"
                                   name="ramon_app_key"
                                   value="<?php echo \esc_attr($appKey); ?>"
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
                                   value="<?php echo \esc_attr($apiUrl); ?>"
                                   class="regular-text"
                                   placeholder="https://example.com/api"
                                   required />
                            <p class="description">The backend API URL for the chatbot.</p>
                        </td>
                    </tr>
                </table>
                <?php \submit_button('Save Settings'); ?>
            </form>
        </div>
        <?php
    }
}
