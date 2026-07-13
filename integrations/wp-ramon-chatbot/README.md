# RAMon Chatbot - WordPress Plugin

WordPress plugin that injects the RAMon AI chatbot bubble into your site.

## Prerequisites

- WordPress 5.0+
- PHP 7.4+
- A running RAMon backend with `APP_KEY`
- The frontend must be built first (`frontend/dist-widget/` must exist)

## Installation

### 1. Copy assets

Before installing the plugin, run the `copy_assets.sh` script to copy the widget assets from the frontend build into the plugin:

```bash
cd integrations/wp-ramon-chatbot
./copy_assets.sh
```

This copies `ramon-burble.js` and font files from `frontend/dist-widget/` into `assets/`. The `assets/` directory is gitignored, so this step is required every time you rebuild the frontend or clone the repo fresh.

### 2. Install on WordPress

1. Zip the `wp-ramon-chatbot` folder (or copy it directly):
   ```bash
   cd integrations
   zip -r wp-ramon-chatbot.zip wp-ramon-chatbot
   ```
2. In WordPress admin, go to **Plugins > Add Plugin > Upload Plugin**.
3. Upload the zip and click **Install Now**.
4. Click **Activate**.

## Configuration

Go to **Settings > RAMon Chatbot** in the WordPress admin.

| Field | Description |
|-------|-------------|
| **App Key** | Shared secret used to sign the JWT token. Must match the `APP_KEY` from the RAMon backend `.env`. |
| **API URL** | Backend API URL (e.g. `https://api.example.com`). Must match the the backend URL. |

Enter both values and click **Save Settings**.

## How It Works

- On every page load, the plugin injects a `__RAMON_CONFIG__` object into the footer with a signed JWT, the API URL, and the assets URL.
- `ramon.js` reads the config and dynamically loads `ramon-burble.js` from the plugin's local `assets/` folder.
- If the page is a WooCommerce product page, the current post ID is included as `productId` in the config.
- The chatbot bubble is rendered on the page automatically.

## Updating Assets

After rebuilding the frontend, re-run the copy script:

```bash
cd integrations/wp-ramon-chatbot
./copy_assets.sh
```

Then reactivate the plugin or re-upload it to WordPress.
