<?php

declare(strict_types=1);

namespace Ramon\Chatbot;

use Ramon\Chatbot\Adapters\WpClock;
use Ramon\Chatbot\Adapters\WpCronScheduler;
use Ramon\Chatbot\Adapters\WpHttpClient;
use Ramon\Chatbot\Adapters\WpInitialSyncRepository;
use Ramon\Chatbot\Adapters\WpOptionStore;
use Ramon\Chatbot\Adapters\WpProductQuery;
use Ramon\Chatbot\Adapters\WpSiteIterator;
use Ramon\Chatbot\Adapters\WpTransientStore;
use Ramon\Chatbot\Admin\SettingsPage;
use Ramon\Chatbot\Services\JwtService;
use Ramon\Chatbot\Services\SyncService;
use Ramon\Chatbot\Sync\InitialSync;
use Ramon\Chatbot\Sync\ProductChangeHandler;

/**
 * Main plugin orchestrator.
 *
 * Wires all dependencies together and registers WordPress hooks.
 * This is the single entry point — all classes are resolved here.
 */
final class Plugin
{
    private WpOptionStore $options;
    private JwtService $jwt;
    private SyncService $sync;
    private ProductChangeHandler $changeHandler;
    private InitialSync $initialSync;
    private SettingsPage $settingsPage;

    /**
     * Build and wire the entire plugin.
     */
    public function boot(string $pluginDir, string $pluginUrl): void
    {
        // Shared infrastructure
        $this->options = new WpOptionStore();
        $clock = new WpClock();
        $http = new WpHttpClient();

        // Services
        $this->jwt = new JwtService($this->options);
        $this->sync = new SyncService($this->options, $http, $this->jwt);

        // Sync handlers
        $extractor = new \Ramon\Chatbot\Adapters\WpProductExtractor();
        $this->changeHandler = new ProductChangeHandler($extractor, $this->sync, $this->options, $clock);
        $this->initialSync = new InitialSync(
            $this->options,
            $clock,
            $this->sync,
            $extractor,
            new WpInitialSyncRepository(),
            new WpCronScheduler(),
            new WpProductQuery(),
            new WpTransientStore(),
            new WpSiteIterator(),
        );

        // Admin
        $this->settingsPage = new SettingsPage($this->options, $this->initialSync);

        // Register hooks
        $this->registerLifecycleHooks();
        $this->registerSyncHooks();
        $this->registerCronHooks();
        $this->registerFrontend($pluginUrl);
        $this->settingsPage->register();
    }

    // ------------------------------------------------------------------
    // Hook registration
    // ------------------------------------------------------------------

    private function registerLifecycleHooks(): void
    {
        \register_activation_hook(RAMON_CHATBOT_PLUGIN_FILE, [$this->initialSync, 'onActivate']);
        \register_deactivation_hook(RAMON_CHATBOT_PLUGIN_FILE, [$this->initialSync, 'onDeactivate']);
    }

    private function registerSyncHooks(): void
    {
        \add_action('woocommerce_update_product', [$this->changeHandler, 'onProductChange'], 10, 2);
        \add_action('woocommerce_new_product', [$this->changeHandler, 'onProductChange'], 10, 2);
        \add_action('before_delete_post', [$this->changeHandler, 'onProductDelete']);
    }

    private function registerCronHooks(): void
    {
        \add_action(InitialSync::cronHook(), [$this->initialSync, 'processCron']);
        \add_action('admin_init', [$this->initialSync, 'maybeDropTable']);

        \add_filter('cron_schedules', static function (array $schedules): array {
            $schedules['one_minute'] = [
                'interval' => 60,
                'display' => \__('Every Minute', 'ramon-chatbot'),
            ];
            return $schedules;
        });
    }

    private function registerFrontend(string $pluginUrl): void
    {
        $jwt = $this->jwt;
        $options = $this->options;

        \add_action('wp_footer', static function () use ($jwt, $options, $pluginUrl): void {
            $appKey = (string) $options->get('ramon_app_key', '');
            $apiUrl = (string) $options->get('ramon_api_url', '');

            if ($appKey === '' || $apiUrl === '') {
                return;
            }

            $token = $jwt->generate();
            $assetsUrl = $pluginUrl . '/assets';
            $productId = self::getProductId();

            $config = [
                'token' => $token,
                'apiUrl' => $apiUrl,
                'assetsUrl' => $assetsUrl,
            ];

            if ($productId !== null) {
                $config['productId'] = (string) $productId;
            }

            $configJson = (string) \wp_json_encode($config);

            echo "<script>window.__RAMON_CONFIG__ = {$configJson};</script>\n";
            echo '<script src="' . \esc_url($pluginUrl . '/assets/ramon.js') . '"></script>' . "\n";
        });
    }

    // ------------------------------------------------------------------
    // Helpers
    // ------------------------------------------------------------------

    /**
     * Get the current product ID if on a WooCommerce product page.
     */
    private static function getProductId(): ?int
    {
        if (\function_exists('is_product') && \is_product()) {
            global $post;
            if ($post instanceof \WP_Post) {
                return $post->ID;
            }
        }
        return null;
    }
}
