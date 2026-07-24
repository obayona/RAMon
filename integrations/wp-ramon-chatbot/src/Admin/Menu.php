<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Admin;

/**
 * Registers the RAMon Chatbot admin menu with Settings and Sync subpages.
 */
final class Menu
{
    private const SLUG = 'ramon-chatbot';
    private const SYNC_SLUG = 'ramon-chatbot-sync';

    public function __construct(
        private readonly SettingsPage $settingsPage,
        private readonly SyncPage $syncPage,
    ) {
    }

    /**
     * Register WordPress admin hooks.
     */
    public function register(): void
    {
        \add_action('admin_menu', [$this, 'addMenus']);
        $this->settingsPage->register();
    }

    /**
     * Add the menu pages.
     */
    public function addMenus(): void
    {
        \add_menu_page(
            'RAMon Settings',
            'RAMon Chatbot',
            'manage_options',
            self::SLUG,
            [$this->settingsPage, 'renderPage'],
            'dashicons-format-chat',
            80,
        );

        \add_submenu_page(
            self::SLUG,
            'RAMon Settings',
            'Settings',
            'manage_options',
            self::SLUG,
            [$this->settingsPage, 'renderPage'],
        );

        \add_submenu_page(
            self::SLUG,
            'RAMon Sync',
            'Sync',
            'manage_options',
            self::SYNC_SLUG,
            [$this->syncPage, 'renderPage'],
        );
    }
}
