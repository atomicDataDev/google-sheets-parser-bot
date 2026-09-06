# Google Sheets Parser Telegram Bot

A standalone, lightweight Telegram bot that automatically monitors a Google Spreadsheet for changes, exports the updated document as a PDF, and sends it directly to your Telegram group, channel, or forum topic.

---

## 🌟 Key Features

* **🔄 Automated Scheduling**: Daily automatic checks (default: 18:00) running in a background thread.
* **⚡ Lightweight Change Detection**: Queries Google Drive API v3 metadata (`modifiedTime`) using only a few bytes per request.
* **📄 Automated PDF Export**: Automatically downloads and dispatches the formatted spreadsheet document upon detecting changes.
* **💬 Telegram Forum / Topics Support**: Seamlessly routes notifications to specific forum threads (`message_thread_id`).
* **🤖 Interactive On-Demand Commands**:
  * `/check` — Manually triggers an immediate update check and replies in the current chat/topic.
  * `/ping` — Checks bot health and displays the timestamp of the last known spreadsheet update.
* **🛡️ Fault Tolerance & Auto-Recovery**: Infinity polling wrapped with automatic retry on network disconnects.
* **🚀 Ready for Standalone Deployment**: Run via Docker, Docker Compose, or as a native Linux `systemd` background service.

---

## 📋 Prerequisites

Before setting up the bot, you will need:

1. **Telegram Bot Token**:
   * Open Telegram and message [@BotFather](https://t.me/BotFather).
   * Send `/newbot` and follow the prompts to get your `BOT_TOKEN`.
2. **Telegram Chat ID & Topic ID**:
   * Add your bot to the target group or supergroup as an Administrator.
   * Send a test message in the group/topic, then get your chat ID (e.g., via [@getidsbot](https://t.me/getidsbot) or by checking `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`).
   * Group chat IDs are typically negative numbers (e.g., `-1001234567890`).
   * If using Telegram forum topics, note the topic ID (`message_thread_id`).
3. **Google Cloud Service Account**:
   * Go to the [Google Cloud Console](https://console.cloud.google.com/).
   * Create a new project (or select an existing one).
   * Navigate to **APIs & Services** > **Library**, search for **Google Drive API**, and click **Enable**.
   * Navigate to **APIs & Services** > **Credentials**, click **Create Credentials** > **Service Account**.
   * After creating the service account, go to the **Keys** tab > **Add Key** > **Create new key** > choose **JSON**. A JSON file will download to your computer.
   * Copy the `client_email` from the JSON key (e.g., `bot-service@project.iam.gserviceaccount.com`).
   * **Important**: Open your Google Spreadsheet, click **Share**, and grant **Viewer** access to the service account email.

---

## ⚙️ Configuration (`.env`)

Create a `.env` file in the root directory by copying `.env.example`:

```bash
cp .env.example .env
```

Fill in the parameters:

| Variable | Required | Description | Example |
| :--- | :---: | :--- | :--- |
| `BOT_TOKEN` | **Yes** | Telegram Bot API token from @BotFather | `1234567890:ABCdefGHI...` |
| `GROUP_CHAT_ID` | **Yes** | Destination Telegram chat or group ID | `-1001234567890` |
| `MESSAGE_THREAD_ID` | No | Topic/Thread ID for forum supergroups | `42` (or leave empty) |
| `SPREADSHEET_ID` | **Yes** | Google Spreadsheet ID from document URL | `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms` |
| `GOOGLE_CREDENTIALS`| **Yes** | Full Google Service Account JSON string in a single line | `{"type":"service_account",...}` |
| `TARGET_SHEETS` | No | Comma-separated sheet names to monitor | `Sheet1,Sheet2` (or leave empty) |

> 💡 **Tip for `GOOGLE_CREDENTIALS`**: Minify your downloaded JSON key into a single line (remove extra line breaks) before pasting it into `.env`.

---

## 🚀 Deployment & Running

### Option 1: Docker & Docker Compose (Recommended)

Docker is the simplest way to run the bot standalone on any server:

1. Clone this repository:
   ```bash
   git clone https://github.com/atomicDataDev/google-sheets-parser-bot.git
   cd google-sheets-parser-bot
   ```

2. Create and configure your `.env` file:
   ```bash
   cp .env.example .env
   nano .env
   ```

3. Start the container in detached background mode:
   ```bash
   docker compose up -d
   ```

4. View logs:
   ```bash
   docker compose logs -f
   ```

5. Stop the bot:
   ```bash
   docker compose down
   ```

---

### Option 2: Linux Systemd Service (VPS Standalone)

To run the bot as a persistent background service managed by Linux `systemd`:

1. Clone the repository and install dependencies:
   ```bash
   cd /opt
   git clone https://github.com/atomicDataDev/google-sheets-parser-bot.git
   cd google-sheets-parser-bot
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Configure `.env`:
   ```bash
   cp .env.example .env
   nano .env
   ```

3. Create the systemd service file:
   ```bash
   sudo cp google-sheets-parser-bot.service.example /etc/systemd/system/google-sheets-parser-bot.service
   sudo nano /etc/systemd/system/google-sheets-parser-bot.service
   ```
   *(Update `User`, `WorkingDirectory`, and `ExecStart` paths if necessary).*

4. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now google-sheets-parser-bot.service
   ```

5. Check status and logs:
   ```bash
   sudo systemctl status google-sheets-parser-bot.service
   journalctl -u google-sheets-parser-bot.service -f
   ```

---

### Option 3: Manual Python Execution

1. Clone the repository:
   ```bash
   git clone https://github.com/atomicDataDev/google-sheets-parser-bot.git
   cd google-sheets-parser-bot
   ```

2. Create a virtual environment and install requirements:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Populate `.env`:
   ```bash
   cp .env.example .env
   nano .env
   ```

4. Run the bot:
   ```bash
   python main.py
   ```

---

## 🕹️ Bot Commands

| Command | Description |
| :--- | :--- |
| `/check` | Manually triggers an update check. If changes are found, exports and sends the PDF. If unchanged, reports current status. |
| `/ping` | Health-check command. Replies with the bot's online status and last detected modification timestamp. |

---

## 🏗️ Architecture & How It Works

```text
┌─────────────────────────────────────────────────────────┐
│                        main.py                          │
│  - Receives /check and /ping commands                   │
│  - Runs background daily schedule (10:00 AM)            │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│                       checker.py                        │
│                     (CheckerLogic)                      │
│  - Orchestrates checks and notifications                │
└──────────────┬─────────────┬────────────────────────────┘
               │             │
      Queries  │             │ Reads & Updates
      Metadata │             │ Timestamp
               ▼             ▼
┌─────────────────────────┐ ┌───────────────────────────┐
│    google_client.py     │ │     state_manager.py      │
│  (Google Drive API v3)  │ │       (state.json)        │
└──────────────┬──────────┘ └───────────────────────────┘
               │
      Downloads PDF
      on change
               ▼
┌─────────────────────────┐
│     pyTelegramBotAPI    │ ───► Sends PDF & updates to Telegram
└─────────────────────────┘
```

1. **Polling Trigger**: Either the daily schedule in `main.py` fires or a user issues `/check`.
2. **Metadata Comparison**: `checker.py` calls `google_client.py` to retrieve `modifiedTime` from Google Drive API v3.
3. **State Evaluation**: `state_manager.py` checks whether the returned `modifiedTime` differs from the timestamp saved in `state.json`.
4. **Export & Delivery**: If a newer timestamp is detected, `google_client.py` exports the spreadsheet as a PDF, and `checker.py` sends it to Telegram via `bot.send_document`.
5. **State Update & Cleanup**: `state.json` is updated with the new timestamp, and the temporary PDF file is safely deleted from disk.

---

## ❓ Frequently Asked Questions & Troubleshooting

<details>
<summary><b>1. Error: <code>google.auth.exceptions.DefaultCredentialsError</code> or invalid credentials</b></summary>

* Ensure that `GOOGLE_CREDENTIALS` in `.env` contains valid JSON.
* Ensure all double quotes inside the JSON string are properly formatted and that the JSON is on a single line.
</details>

<details>
<summary><b>2. Error: 403 Forbidden / "The caller does not have permission"</b></summary>

* Verify that you shared the Google Spreadsheet with the service account email (found in the `client_email` field of your JSON key) with **Viewer** permissions.
</details>

<details>
<summary><b>3. Error: 400 / 401 Unauthorized from Telegram</b></summary>

* Check that `BOT_TOKEN` in `.env` is exact and valid.
* Ensure the bot has been added to the target group and has permissions to send messages and documents.
</details>

<details>
<summary><b>4. How do I change the daily check time?</b></summary>

* Open `main.py` and modify the time string in `schedule.every().day.at("10:00").do(checker.check_updates)`.
</details>

---

## 📄 License

This project is open source and available under the terms of the [MIT License](LICENSE).
