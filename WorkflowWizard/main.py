#!/usr/bin/env python3
"""
Advanced Telethon Session Manager

This is a Flask application that provides a status page for the bot.
The actual bot runs separately through simple_bot.py and provides
secure management of Telethon session strings with enhanced privacy features.
"""
import os
import sys
import logging
import subprocess
import threading
import time
from flask import Flask, render_template_string

# Create a Flask app
app = Flask(__name__)

# Disable Flask logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Configure our own logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global variable to track the bot process
bot_process = None

@app.route('/')
def index():
    """Main route that shows the bot status"""
    template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Advanced Telethon Session Manager</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
        <style>
            .container {
                max-width: 800px;
                margin-top: 50px;
            }
            .card {
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body data-bs-theme="dark">
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2>Advanced Telethon Session Manager</h2>
                </div>
                <div class="card-body">
                    <h4 class="text-success">✅ Bot is running</h4>
                    <p>The Telegram bot is actively running in the background.</p>
                    
                    <h5>Key Features:</h5>
                    <ul>
                        <li><strong>Button-based Interface</strong> - No need to memorize commands</li>
                        <li><strong>Multiple Session Management</strong> - Create and organize session strings</li>
                        <li><strong>Session Validation</strong> - Check if your sessions are still valid</li>
                        <li><strong>Comprehensive Security</strong> - Auto-delete phone numbers, codes, and passwords</li>
                        <li><strong>Privacy Protection</strong> - Multiple layers of security for sensitive data</li>
                    </ul>
                    
                    <h5>Enhanced Security Features:</h5>
                    <ul>
                        <li><strong>Automatic Deletion</strong> - Phone numbers deleted after processing</li>
                        <li><strong>Code Protection</strong> - Verification codes removed immediately after submission</li>
                        <li><strong>Password Security</strong> - 2FA passwords never stored in chat history</li>
                        <li><strong>Configurable Settings</strong> - Customize security to your preferences</li>
                        <li><strong>Session Auto-Delete</strong> - Option to auto-delete session strings after 5 minutes</li>
                    </ul>
                    <p>To use the bot:</p>
                    <ol>
                        <li>Open Telegram and search for your bot (using the username you configured with BotFather)</li>
                        <li>Start a conversation with the bot by pressing the START button</li>
                        <li>Use the interactive buttons to navigate the interface</li>
                        <li>Generate and manage your session strings securely</li>
                    </ol>
                    <div class="alert alert-warning">
                        <h5><i class="bi bi-exclamation-triangle-fill"></i> Security Warning</h5>
                        <p><strong>Important:</strong> Session strings provide full access to Telegram accounts. Never share them with anyone!</p>
                        <p>Our enhanced security features help protect your sensitive information by automatically deleting:</p>
                        <ul class="mb-0">
                            <li>Phone numbers (immediately after processing)</li>
                            <li>Verification codes (once submitted)</li>
                            <li>2FA passwords (after verification)</li>
                            <li>Session strings (optionally after 5 minutes, when enabled)</li>
                        </ul>
                    </div>
                </div>
                <div class="card-footer text-muted">
                    <div class="d-flex justify-content-between align-items-center">
                        <span>Features: Advanced Security, Multi-Session Management, Validation, Privacy Protection</span>
                        <span class="badge bg-success">Enhanced Security Enabled</span>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(template)

def start_bot_process():
    """Start the bot process"""
    global bot_process
    try:
        # Check if TELEGRAM_BOT_TOKEN is set
        if not os.environ.get("TELEGRAM_BOT_TOKEN"):
            logger.error("TELEGRAM_BOT_TOKEN not set")
            return

        logger.info("Starting Telegram bot process...")
        bot_process = subprocess.Popen(["python", "simple_bot.py"], stderr=subprocess.PIPE)
        logger.info(f"Bot process started with PID: {bot_process.pid}")
    except Exception as e:
        logger.error(f"Error starting bot process: {e}")

def monitor_bot_process():
    """Monitor the bot process and restart if needed"""
    global bot_process
    
    while True:
        # Check if the process is still running
        if bot_process is None or bot_process.poll() is not None:
            logger.warning("Bot process not running, attempting to restart...")
            start_bot_process()
        
        # Wait before checking again
        time.sleep(30)

# Start the bot process
start_bot_process()

# Start the monitoring thread
monitor_thread = threading.Thread(target=monitor_bot_process)
monitor_thread.daemon = True
monitor_thread.start()

# Start the Flask app
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
