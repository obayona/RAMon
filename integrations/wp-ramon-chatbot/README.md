# RAMon Chatbot — WordPress Plugin

WordPress/WooCommerce plugin that injects the RAMon AI chatbot widget and syncs product data to the backend.

## Features

- **Chatbot widget** — Injects the RAMon chatbot bubble on every page via a signed JWT config.
- **Real-time product sync** — Sends upsert/delete events to the backend whenever a WooCommerce product is created, updated, or deleted.
- **Initial bulk sync** — On activation, queues all published products for sync via WP-Cron batches. Progress is visible in the admin UI.
- **Admin settings** — Configure App Key, API URL, and monitor sync progress with a percentage bar and retry failed products.

## Prerequisites

- WordPress 5.0+ with WooCommerce
- PHP 8.1+
- Composer
- A running RAMon backend with `APP_KEY`
- The frontend must be built first (`frontend/dist-widget/` must exist)

## Installation

### 1. Install dependencies

```bash
cd integrations/wp-ramon-chatbot
composer install
```

This installs PHP packages, generates the PSR-4 autoloader, and copies frontend assets into `assets/` automatically via the `post-install-cmd` script.

### 2. Install on WordPress

1. Zip the plugin folder:
   ```bash
   cd integrations
   zip -r wp-ramon-chatbot.zip wp-ramon-chatbot
   ```
2. In WordPress admin, go to **Plugins > Add Plugin > Upload Plugin**.
3. Upload the zip and click **Install Now**.
4. Click **Activate**.

On activation, the plugin schedules an initial product sync. Progress is shown under **Settings > RAMon Chatbot**.

## Configuration

Go to **Settings > RAMon Chatbot** in the WordPress admin.

| Field | Description |
|-------|-------------|
| **App Key** | Shared secret used to sign the JWT token. Must match the `APP_KEY` from the RAMon backend `.env`. |
| **API URL** | Backend API URL (e.g. `https://api.example.com`). Must match the backend URL. |

## Architecture

```
ramon-chatbot.php              # Plugin bootstrap (minimal)
src/
├── Plugin.php                 # Orchestrator — wires all dependencies
├── Domain/
│   ├── ProductData.php        # Immutable product DTO
│   └── SyncStatus.php         # Immutable sync status DTO
├── Ports/                     # Interfaces (dependency inversion)
│   ├── OptionStore.php        # Abstraction for WP options
│   ├── HttpClient.php         # Abstraction for HTTP requests
│   ├── Clock.php              # Abstraction for time
│   └── ProductExtractor.php   # Abstraction for WC product extraction
├── Adapters/                  # WordPress implementations
│   ├── WpOptionStore.php
│   ├── WpHttpClient.php
│   ├── WpClock.php
│   └── WpProductExtractor.php
├── Services/
│   ├── JwtService.php         # Stateless JWT generation (HMAC-SHA256)
│   └── SyncService.php        # Sends product changes to backend API
├── Sync/
│   ├── ProductChangeHandler.php  # WC hook handlers (create/update/delete)
│   └── InitialSync.php           # Bulk sync on activation via WP-Cron
└── Admin/
    └── SettingsPage.php       # Admin settings UI with sync progress
```

All business logic depends on interfaces (`Ports/`), not WordPress functions directly. WordPress-specific code lives in `Adapters/`. This makes the core logic testable without a WP environment.

## Development

### Linting

PHPStan (level 6):

```bash
composer analyse
# or
vendor/bin/phpstan analyse
```

### Testing

PHPUnit:

```bash
composer test
# or
vendor/bin/phpunit
```

Tests use hand-crafted mocks in `tests/Mocks/` that implement the same interfaces as the WP adapters. No WordPress installation required.

### Updating assets

After rebuilding the frontend, re-run the copy script:

```bash
composer post-install-cmd
# or
bash copy_assets.sh
```

## How It Works

### Frontend widget

On every page load, the plugin injects a `window.__RAMON_CONFIG__` object into the footer with a signed JWT, the API URL, and the assets URL. `ramon.js` reads the config and dynamically loads `ramon-burble.js`. If the page is a WooCommerce product page, the current post ID is included as `productId`.

### Product sync

WooCommerce hooks (`woocommerce_new_product`, `woocommerce_update_product`, `before_delete_post`) trigger the `ProductChangeHandler`, which extracts product data via `WpProductExtractor` and sends it to the backend's `POST /api/sync/products` endpoint via `SyncService`.

### Initial sync

On plugin activation, `InitialSync` sets a flag (no heavy work). A WP-Cron job (`ramon_initial_sync_hook`) fires every minute, creates a temporary database table with all published product IDs, and processes them in batches of 10. Each batch fetches live WooCommerce data, sends it to the backend, and marks products as done or error. The table is dropped once all products are synced. A "Retry Failed Products" button is available in the admin UI.
