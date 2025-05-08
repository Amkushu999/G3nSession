# Advanced Telethon Session Manager

A feature-rich Telegram bot that helps users generate and manage Telethon session strings. It provides an intuitive button-based interface for seamless interaction without needing to memorize commands.

## Features

### Core Functionality
- Generates Telethon session strings for Telegram users
- Button-based interface with no slash commands required
- Handles phone number input with validation
- Processes verification codes securely
- Supports two-factor authentication
- Displays user account information

### Advanced Features
- **Multiple Session Management**: Create and store multiple session strings
- **Custom Labels**: Name your sessions for easy identification
- **Session Validation**: Check if your saved sessions are still valid
- **Account Info**: View associated account details for each session
- **Security Controls**: Auto-delete sensitive messages after viewing
- **Simplified Navigation**: Intuitive menu system for all operations

## Requirements

- Python 3.7+
- `telethon` library
- `flask` (for status web interface)
- Environment with persistent storage

## Setup

1. Clone this repository
2. Install the requirements
3. Set up the required environment variable:
   - `TELEGRAM_BOT_TOKEN`: Your Telegram Bot Token from BotFather

4. The bot automatically uses these API credentials:
   - API ID: 20584497
   - API Hash: 73dcd3a22805af2f3d5c2693475c1746

5. Run the bot:
   ```
   python main.py
   ```

## Usage

1. Open Telegram and find your bot
2. Press the START button to begin interaction
3. Use the menu buttons to:
   - Generate a new session string
   - View and manage existing sessions
   - Toggle security settings
   - Get help information

## Security Notes

- Session strings provide full access to a Telegram account - handle with extreme caution
- The auto-delete feature helps protect sensitive information in chat history
- All session data is stored locally on the device running the bot
- Never share session strings with anyone you don't trust completely
- This bot is designed with security in mind, offering:
  - Message deletion for sensitive content
  - Secure storage of session information
  - Clear warnings about the power of session strings
  - Option to validate sessions before using them

## License

MIT License
