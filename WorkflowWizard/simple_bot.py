#!/usr/bin/env python3
"""
Advanced Telethon Session Manager

A feature-rich bot for generating and managing Telethon session strings,
with multiple session support, validation features, and enhanced security.
"""
import os
import sys
import time
import logging
import asyncio
import datetime
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.errors import (
    PhoneCodeInvalidError, 
    PhoneCodeExpiredError, 
    SessionPasswordNeededError,
    PasswordHashInvalidError,
    AuthKeyUnregisteredError,
    UserDeactivatedError
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Telegram API credentials - confirmed by user
API_ID = 20584497
API_HASH = "73dcd3a22805af2f3d5c2693475c1746"

# Device model for session info
DEVICE_MODEL = "Advanced Telethon Session Manager"

# Settings for auto-deletion of messages containing sensitive data
auto_delete_settings = {}

# Bot token from environment
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
    print("Error: No Telegram bot token found! Please set the TELEGRAM_BOT_TOKEN environment variable.")
    print("You can get a token from @BotFather on Telegram.")
    sys.exit(1)

# Create the bot client
bot = TelegramClient('simple_bot', API_ID, API_HASH)

# Store active sessions - simple key/value storage
active_processes = {}

# Store saved sessions
saved_sessions = {}

@bot.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    """Handler for /start command"""
    # Clear any existing process for this user
    user_id = event.sender_id
    if user_id in active_processes:
        # Clean up any existing clients
        if 'client' in active_processes[user_id]:
            try:
                client = active_processes[user_id]['client']
                if client:
                    await client.disconnect()
            except:
                pass
        # Remove the data
        del active_processes[user_id]
    
    # Create main menu with buttons
    markup = [
        [Button.inline('📱 Generate New Session', b'start_session')],
        [Button.inline('🔍 Check Session Validity', b'check_session')],
        [Button.inline('📋 View My Sessions', b'view_sessions')],
        [Button.inline('🔒 Auto-Delete Messages', b'toggle_autodelete')],
        [Button.inline('❓ Help', b'show_help')]
    ]

    await event.respond(
        "🔐 *Advanced Telethon Session Manager* 🔐\n\n"
        "This bot helps you generate, validate, and manage multiple Telethon session strings with enhanced security features.\n\n"
        "Select an option from the menu below:",
        buttons=markup,
        parse_mode='Markdown'
    )

@bot.on(events.CallbackQuery(data=b'start_session'))
async def start_session(event):
    """Start the session generation process"""
    # Edit the button message to ask for the phone number
    msg = await event.edit(
        "📱 Please send your phone number in international format.\n"
        "Example: +12345678900"
    )
    
    # Store a flag to recognize the next message as phone number
    user_id = event.sender_id
    active_processes[user_id] = {
        'expecting': 'phone',
        'status_msg': msg  # Save the message to edit it later
    }

@bot.on(events.NewMessage)
async def message_handler(event):
    """Handle all incoming messages based on user state"""
    user_id = event.sender_id
    
    # If no active process for this user, ignore
    if user_id not in active_processes:
        return
    
    # Get what we're expecting from this user
    expecting = active_processes[user_id].get('expecting')
    
    # Handle based on what we're expecting
    if expecting == 'phone':
        await handle_phone(event, user_id)
    elif expecting == 'code':
        await handle_code(event, user_id)
    elif expecting == 'password':
        await handle_password(event, user_id)
    elif expecting == 'session_string_to_check':
        await handle_session_validation(event, user_id)
    elif expecting == 'session_label':
        await handle_session_label(event, user_id)
        
async def handle_session_validation(event, user_id):
    """Handle session string validation"""
    session_string = event.text.strip()
    
    if not session_string:
        await event.respond("Please provide a valid session string.")
        return
    
    # Save the status message for updating throughout the process
    msg = await event.respond("🔍 Validating session string...")
    active_processes[user_id]['status_msg'] = msg
    
    try:
        # Create client with the session string
        client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
        await client.connect()
        
        # Check if the session is valid
        if await client.is_user_authorized():
            # Get user info
            me = await client.get_me()
            user_name = f"{me.first_name} {me.last_name if me.last_name else ''}".strip()
            username_text = f"@{me.username}" if me.username else "No username"
            
            await msg.edit(
                f"✅ *Session is valid!*\n\n"
                f"*Account Information:*\n"
                f"👤 User: {user_name}\n"
                f"🔖 Username: {username_text}\n"
                f"🆔 User ID: `{me.id}`\n\n"
                f"This session is currently active and can be used.",
                buttons=[[Button.inline('🔙 Back to Main Menu', b'back_to_menu')]],
                parse_mode='Markdown'
            )
        else:
            await msg.edit(
                "❌ *Session is not valid*\n\n"
                "The session string you provided is not authorized.\n"
                "This could happen if the session was revoked or expired.",
                buttons=[[Button.inline('🔙 Back to Main Menu', b'back_to_menu')]],
                parse_mode='Markdown'
            )
            
        # Clean up client
        await client.disconnect()
        
    except (AuthKeyUnregisteredError, UserDeactivatedError):
        await msg.edit(
            "❌ *Session is invalid*\n\n"
            "This session string has been revoked or the account has been deactivated.",
            buttons=[[Button.inline('🔙 Back to Main Menu', b'back_to_menu')]],
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error validating session: {e}")
        await msg.edit(
            f"❌ *Error validating session*\n\n"
            f"An error occurred: {str(e)}",
            buttons=[[Button.inline('🔙 Back to Main Menu', b'back_to_menu')]],
            parse_mode='Markdown'
        )
        
    # Clear user state
    if user_id in active_processes:
        del active_processes[user_id]
        
async def handle_session_label(event, user_id):
    """Handle custom session labeling"""
    label = event.text.strip()
    
    if not label:
        await event.respond("Please provide a valid label for your session.")
        return
        
    # Get the session index
    session_index = active_processes[user_id].get('session_index', 0)
    
    # Update the label
    if user_id in saved_sessions and session_index < len(saved_sessions[user_id]):
        saved_sessions[user_id][session_index]['label'] = label
        
        await event.respond(
            f"✅ Session renamed to: *{label}*",
            buttons=[[Button.inline('🔙 Back to Main Menu', b'back_to_menu')]],
            parse_mode='Markdown'
        )
    else:
        await event.respond(
            "❌ Session not found. Please try again.",
            buttons=[[Button.inline('🔙 Back to Main Menu', b'back_to_menu')]]
        )
        
    # Clear user state
    if user_id in active_processes:
        del active_processes[user_id]

async def handle_phone(event, user_id):
    """Handle phone number input"""
    phone = event.text.strip()
    
    if not phone.startswith('+'):
        await event.respond("Please provide a valid phone number starting with +")
        return
    
    # Store phone number
    active_processes[user_id]['phone'] = phone
    active_processes[user_id]['expecting'] = 'code'
    
    # Delete the phone number message for security
    try:
        await event.delete()
    except Exception as e:
        logger.warning(f"Could not delete phone message: {e}")
    
    # Get the existing status message or create a new one
    msg = active_processes[user_id].get('status_msg')
    if msg:
        try:
            await msg.edit("📲 Requesting verification code... (Your phone number has been deleted from chat for security)")
        except Exception as e:
            logger.warning(f"Could not edit status message: {e}")
            msg = await event.respond("📲 Requesting verification code... (Your phone number has been deleted from chat for security)")
    else:
        msg = await event.respond("📲 Requesting verification code... (Your phone number has been deleted from chat for security)")
    
    # Update the status message reference
    active_processes[user_id]['status_msg'] = msg
    
    try:
        # Create new client
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()
        
        # Store client
        active_processes[user_id]['client'] = client
        
        # Request verification code
        await client.send_code_request(phone)
        
        await msg.edit(
            "✅ Verification code sent!\n\n"
            "Please enter the verification code you received.\n"
            "You can add spaces between digits if needed (e.g. `1 2 3 4 5`)",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error sending code request: {e}")
        await msg.edit(f"❌ Error requesting verification code: {str(e)}")
        del active_processes[user_id]

async def handle_code(event, user_id):
    """Handle verification code input"""
    code = event.text.strip()
    
    # Remove any non-digits
    clean_code = ''.join(c for c in code if c.isdigit())
    
    if not clean_code:
        await event.respond("Please provide a valid verification code containing digits.")
        return
    
    phone = active_processes[user_id].get('phone')
    client = active_processes[user_id].get('client')
    
    if not client:
        await event.respond("Session expired. Please start again with /start")
        del active_processes[user_id]
        return
    
    # Delete the verification code message for security
    try:
        await event.delete()
    except Exception as e:
        logger.warning(f"Could not delete verification code message: {e}")
    
    # Get the existing status message or create a new one
    msg = active_processes[user_id].get('status_msg')
    if msg:
        try:
            await msg.edit("🔄 Verifying code and generating session... (Your verification code has been deleted from chat for security)")
        except Exception as e:
            logger.warning(f"Could not edit status message: {e}")
            msg = await event.respond("🔄 Verifying code and generating session... (Your verification code has been deleted from chat for security)")
    else:
        msg = await event.respond("🔄 Verifying code and generating session... (Your verification code has been deleted from chat for security)")
    
    # Update the status message reference
    active_processes[user_id]['status_msg'] = msg
    
    try:
        # Make sure client is connected
        if not client.is_connected():
            await client.connect()
        
        try:
            # Try to sign in with code
            await client.sign_in(phone=phone, code=clean_code)
            
            # Success - get session string
            me = await client.get_me()
            session_string = client.session.save()
            
            # Format response
            user_name = f"{me.first_name} {me.last_name if me.last_name else ''}".strip()
            username_text = f"@{me.username}" if me.username else ""
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Save the session
            if user_id not in saved_sessions:
                saved_sessions[user_id] = []
                
            session_info = {
                'string': session_string,
                'phone': phone,
                'user_info': {
                    'name': user_name,
                    'username': me.username,
                    'id': me.id
                },
                'created_at': current_time,
                'device': f"Telethon {DEVICE_MODEL}",
                'label': f"Session {len(saved_sessions[user_id]) + 1}"
            }
            
            saved_sessions[user_id].append(session_info)
            
            # Generate options to save and manage the session
            markup = [
                [Button.inline('📋 Save with Custom Label', b'label_session')],
                [Button.inline('🔙 Back to Main Menu', b'back_to_menu')],
                [Button.inline('🔄 Generate Another Session', b'start_session')]
            ]
            
            await msg.edit(
                f"✅ Session generated successfully!\n\n"
                f"📱 User: {user_name}\n"
                f"{username_text}\n"
                f"🆔 ID: {me.id}\n"
                f"☎️ Phone: {phone}\n\n"
                f"🔐 Session String:\n`{session_string}`\n\n"
                f"⚠️ *IMPORTANT*: This session string gives full access to your account. "
                f"Never share it with anyone!\n\n"
                f"Your session was automatically saved. You can access it later from the main menu.",
                buttons=markup,
                parse_mode='Markdown'
            )
            
            # Set timer for auto-deletion if enabled
            if user_id in auto_delete_settings and auto_delete_settings[user_id]:
                # Schedule message deletion in 5 minutes
                asyncio.create_task(auto_delete_message(msg, 300))
            
            # Clean up
            await client.disconnect()
            del active_processes[user_id]
            
        except PhoneCodeInvalidError:
            await msg.edit(
                "❌ Invalid verification code.\n\n"
                "Please try again with the correct code."
            )
            # Keep expecting code
            active_processes[user_id]['expecting'] = 'code'
            
        except PhoneCodeExpiredError:
            await msg.edit(
                "❌ Verification code expired.\n\n"
                "Please restart with /start"
            )
            # Clean up
            await client.disconnect()
            del active_processes[user_id]
            
        except SessionPasswordNeededError:
            await msg.edit(
                "🔐 Two-factor authentication is enabled.\n\n"
                "Please enter your 2FA password:"
            )
            # Now expecting password
            active_processes[user_id]['expecting'] = 'password'
            
        except Exception as e:
            logger.error(f"Error signing in with code: {e}")
            await msg.edit(
                f"❌ Error verifying code: {str(e)}\n\n"
                f"Please try again or restart with /start"
            )
            # Keep expecting code in case they want to retry
            active_processes[user_id]['expecting'] = 'code'
            
    except Exception as e:
        logger.error(f"Connection error in code handler: {e}")
        await msg.edit(
            f"❌ Connection error: {str(e)}\n\n"
            f"Please restart with /start"
        )
        # Clean up
        if client:
            await client.disconnect()
        del active_processes[user_id]

async def handle_password(event, user_id):
    """Handle 2FA password input"""
    password = event.text.strip()
    
    if not password:
        await event.respond("Please provide your 2FA password.")
        return
    
    client = active_processes[user_id].get('client')
    phone = active_processes[user_id].get('phone')
    
    if not client:
        await event.respond("Session expired. Please start again with /start")
        del active_processes[user_id]
        return
    
    # Delete the 2FA password message for security
    try:
        await event.delete()
    except Exception as e:
        logger.warning(f"Could not delete 2FA password message: {e}")
    
    # Get the existing status message or create a new one
    msg = active_processes[user_id].get('status_msg')
    if msg:
        try:
            await msg.edit("🔐 Verifying 2FA password... (Your password has been deleted from chat for security)")
        except Exception as e:
            logger.warning(f"Could not edit status message: {e}")
            msg = await event.respond("🔐 Verifying 2FA password... (Your password has been deleted from chat for security)")
    else:
        msg = await event.respond("🔐 Verifying 2FA password... (Your password has been deleted from chat for security)")
    
    # Update the status message reference
    active_processes[user_id]['status_msg'] = msg
    
    try:
        # Make sure client is connected
        if not client.is_connected():
            await client.connect()
        
        # Try to sign in with password
        await client.sign_in(password=password)
        
        # Success - get session string
        me = await client.get_me()
        session_string = client.session.save()
        
        # Format response
        user_name = f"{me.first_name} {me.last_name if me.last_name else ''}".strip()
        username_text = f"@{me.username}" if me.username else ""
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Save the session
        if user_id not in saved_sessions:
            saved_sessions[user_id] = []
            
        session_info = {
            'string': session_string,
            'phone': phone,
            'user_info': {
                'name': user_name,
                'username': me.username,
                'id': me.id
            },
            'created_at': current_time,
            'device': f"Telethon {DEVICE_MODEL}",
            'label': f"Session {len(saved_sessions[user_id]) + 1} (2FA)"
        }
        
        saved_sessions[user_id].append(session_info)
        
        # Generate options to save and manage the session
        markup = [
            [Button.inline('📋 Save with Custom Label', b'label_session')],
            [Button.inline('🔙 Back to Main Menu', b'back_to_menu')],
            [Button.inline('🔄 Generate Another Session', b'start_session')]
        ]
        
        await msg.edit(
            f"✅ Session generated successfully!\n\n"
            f"📱 User: {user_name}\n"
            f"{username_text}\n"
            f"🆔 ID: {me.id}\n"
            f"☎️ Phone: {phone}\n\n"
            f"🔐 Session String:\n`{session_string}`\n\n"
            f"⚠️ *IMPORTANT*: This session string gives full access to your account. "
            f"Never share it with anyone!\n\n"
            f"Your session was automatically saved. You can access it later from the main menu.",
            buttons=markup,
            parse_mode='Markdown'
        )
        
        # Set timer for auto-deletion if enabled
        if user_id in auto_delete_settings and auto_delete_settings[user_id]:
            # Schedule message deletion in 5 minutes
            asyncio.create_task(auto_delete_message(msg, 300))
        
        # Clean up
        await client.disconnect()
        del active_processes[user_id]
        
    except PasswordHashInvalidError:
        await msg.edit(
            "❌ Invalid 2FA password.\n\n"
            "Please try again with the correct password."
        )
        # Keep expecting password
        active_processes[user_id]['expecting'] = 'password'
        
    except Exception as e:
        logger.error(f"Error in password handler: {e}")
        await msg.edit(
            f"❌ Error with 2FA password: {str(e)}\n\n"
            f"Please try again or restart with /start"
        )
        # Keep expecting password in case they want to retry
        active_processes[user_id]['expecting'] = 'password'

# Auto-delete message helper function
async def auto_delete_message(message, delay_seconds):
    """Delete a message after a specific delay"""
    await asyncio.sleep(delay_seconds)
    try:
        await message.delete()
    except Exception as e:
        logger.error(f"Failed to auto-delete message: {e}")

@bot.on(events.CallbackQuery(data=b'back_to_menu'))
async def back_to_menu(event):
    """Handle back to menu button"""
    user_id = event.sender_id
    
    # Clean up any active processes
    if user_id in active_processes:
        if 'client' in active_processes[user_id]:
            try:
                client = active_processes[user_id]['client']
                if client:
                    await client.disconnect()
            except:
                pass
        del active_processes[user_id]
    
    # Show main menu
    markup = [
        [Button.inline('📱 Generate New Session', b'start_session')],
        [Button.inline('🔍 Check Session Validity', b'check_session')],
        [Button.inline('📋 View My Sessions', b'view_sessions')],
        [Button.inline('🔒 Auto-Delete Messages', b'toggle_autodelete')],
        [Button.inline('❓ Help', b'show_help')]
    ]
    
    await event.edit(
        "🔐 *Advanced Telethon Session Manager* 🔐\n\n"
        "This bot helps you generate, validate, and manage multiple Telethon session strings with enhanced security features.\n\n"
        "Select an option from the menu below:",
        buttons=markup,
        parse_mode='Markdown'
    )

@bot.on(events.CallbackQuery(data=b'toggle_autodelete'))
async def toggle_autodelete(event):
    """Toggle auto-delete for security"""
    user_id = event.sender_id
    
    # Toggle setting
    auto_delete_settings[user_id] = not auto_delete_settings.get(user_id, False)
    
    status = "✅ Enabled" if auto_delete_settings[user_id] else "❌ Disabled"
    
    markup = [[Button.inline('🔙 Back to Main Menu', b'back_to_menu')]]
    
    await event.edit(
        f"🔒 *Auto-Delete Security* 🔒\n\n"
        f"Auto-deletion of messages containing sensitive data is now:\n"
        f"*{status}*\n\n"
        f"Security features:\n"
        f"• Phone numbers are always deleted immediately after processing\n"
        f"• Verification codes are always deleted after submission\n"
        f"• 2FA passwords are always deleted for maximum security\n"
        f"• Session strings will be automatically deleted after 5 minutes when this setting is enabled",
        buttons=markup,
        parse_mode='Markdown'
    )

@bot.on(events.CallbackQuery(data=b'view_sessions'))
async def view_sessions(event):
    """View saved sessions"""
    user_id = event.sender_id
    
    # Check if user has saved sessions
    if user_id not in saved_sessions or not saved_sessions[user_id]:
        markup = [[Button.inline('🔙 Back to Main Menu', b'back_to_menu')]]
        await event.edit(
            "📋 *Your Saved Sessions* 📋\n\n"
            "You don't have any saved sessions yet.\n\n"
            "Generate a new session to get started.",
            buttons=markup,
            parse_mode='Markdown'
        )
        return
    
    # List all sessions
    session_list = []
    markup = []
    
    for i, session in enumerate(saved_sessions[user_id]):
        label = session.get('label', f"Session {i+1}")
        created = session.get('created_at', 'Unknown date')
        phone = session.get('phone', 'Unknown')
        
        session_list.append(
            f"{i+1}. *{label}*\n"
            f"   📱 Phone: `{phone}`\n"
            f"   🕒 Created: {created}"
        )
        
        # Add button for this session
        markup.append([Button.inline(f"🔍 Manage Session #{i+1}", f"manage_session_{i}".encode())])
    
    # Add back button
    markup.append([Button.inline('🔙 Back to Main Menu', b'back_to_menu')])
    
    await event.edit(
        "📋 *Your Saved Sessions* 📋\n\n" + 
        "\n\n".join(session_list) + 
        "\n\nClick on a session to manage it:",
        buttons=markup,
        parse_mode='Markdown'
    )

@bot.on(events.CallbackQuery(data=b'label_session'))
async def label_session_request(event):
    """Request a label for the most recent session"""
    user_id = event.sender_id
    
    # Check if user has sessions
    if user_id not in saved_sessions or not saved_sessions[user_id]:
        await event.edit(
            "❌ No session found to label.",
            buttons=[[Button.inline('🔙 Back to Main Menu', b'back_to_menu')]]
        )
        return
    
    # Set session index to the most recent one
    session_index = len(saved_sessions[user_id]) - 1
    
    # Store the index and set state
    active_processes[user_id] = {
        'expecting': 'session_label',
        'session_index': session_index
    }
    
    await event.edit(
        "📝 *Custom Session Label* 📝\n\n"
        "Please send a name for this session. This will help you identify it later.\n\n"
        "Examples: 'Main Account', 'Business Account', 'Bot Development'",
        buttons=[[Button.inline('🔙 Cancel', b'back_to_menu')]],
        parse_mode='Markdown'
    )

# Pattern for session management buttons
@bot.on(events.CallbackQuery(pattern=r"manage_session_(\d+)"))
async def manage_session(event):
    """Manage a specific session"""
    user_id = event.sender_id
    
    # Extract session index from the button data
    session_index = int(event.data.decode().split('_')[-1])
    
    # Validate session index
    if user_id not in saved_sessions or session_index >= len(saved_sessions[user_id]):
        await event.edit(
            "❌ Session not found. It may have been deleted.",
            buttons=[[Button.inline('🔙 Back to Main Menu', b'back_to_menu')]]
        )
        return
    
    # Get session info
    session = saved_sessions[user_id][session_index]
    label = session.get('label', f"Session {session_index+1}")
    created = session.get('created_at', 'Unknown date')
    phone = session.get('phone', 'Unknown')
    username = session.get('user_info', {}).get('username', 'Unknown')
    name = session.get('user_info', {}).get('name', 'Unknown')
    
    # Create buttons for session management
    markup = [
        [Button.inline('✅ Verify Session', f"verify_session_{session_index}".encode())],
        [Button.inline('📋 Show Session String', f"show_session_{session_index}".encode())],
        [Button.inline('✏️ Edit Label', f"edit_label_{session_index}".encode())],
        [Button.inline('❌ Delete Session', f"delete_session_{session_index}".encode())],
        [Button.inline('🔙 Back to Sessions', b'view_sessions')],
        [Button.inline('🔙 Main Menu', b'back_to_menu')]
    ]
    
    await event.edit(
        f"🔐 *Session: {label}* 🔐\n\n"
        f"📱 Phone: `{phone}`\n"
        f"👤 User: {name}\n"
        f"🔖 Username: {username}\n"
        f"🕒 Created: {created}\n\n"
        f"Select an action to perform with this session:",
        buttons=markup,
        parse_mode='Markdown'
    )

@bot.on(events.CallbackQuery(pattern=r"verify_session_(\d+)"))
async def verify_session(event):
    """Verify if a saved session is still valid"""
    user_id = event.sender_id
    session_index = int(event.data.decode().split('_')[-1])
    
    # Validate session index
    if user_id not in saved_sessions or session_index >= len(saved_sessions[user_id]):
        await event.edit(
            "❌ Session not found. It may have been deleted.",
            buttons=[[Button.inline('🔙 Back to Main Menu', b'back_to_menu')]]
        )
        return
    
    # Get session info
    session = saved_sessions[user_id][session_index]
    session_string = session.get('string', '')
    label = session.get('label', f"Session {session_index+1}")
    
    if not session_string:
        await event.edit(
            "❌ Invalid session data. Please generate a new session.",
            buttons=[[Button.inline('🔙 Back to Sessions', b'view_sessions')]]
        )
        return
    
    # Show validation message
    msg = await event.edit(
        f"🔄 Verifying session *{label}*...",
        parse_mode='Markdown'
    )
    
    try:
        # Create client and check validity
        client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
        await client.connect()
        
        if await client.is_user_authorized():
            # Get updated user info
            me = await client.get_me()
            user_name = f"{me.first_name} {me.last_name if me.last_name else ''}".strip()
            username_text = f"@{me.username}" if me.username else "No username"
            
            # Update session info with latest data
            saved_sessions[user_id][session_index]['user_info'] = {
                'name': user_name,
                'username': me.username,
                'id': me.id
            }
            
            await msg.edit(
                f"✅ *Session is valid!*\n\n"
                f"*{label}* is active and can be used.\n\n"
                f"👤 User: {user_name}\n"
                f"🔖 Username: {username_text}",
                buttons=[
                    [Button.inline('🔙 Back to Session', f"manage_session_{session_index}".encode())],
                    [Button.inline('🔙 Back to Main Menu', b'back_to_menu')]
                ],
                parse_mode='Markdown'
            )
        else:
            await msg.edit(
                f"❌ *Session is not valid*\n\n"
                f"*{label}* is no longer authorized.\n"
                f"This could happen if the session was revoked or expired.",
                buttons=[
                    [Button.inline('❌ Delete Session', f"delete_session_{session_index}".encode())],
                    [Button.inline('🔙 Back to Session', f"manage_session_{session_index}".encode())],
                    [Button.inline('🔙 Back to Main Menu', b'back_to_menu')]
                ],
                parse_mode='Markdown'
            )
        
        # Clean up
        await client.disconnect()
        
    except (AuthKeyUnregisteredError, UserDeactivatedError):
        await msg.edit(
            f"❌ *Session is invalid*\n\n"
            f"*{label}* has been revoked or the account has been deactivated.",
            buttons=[
                [Button.inline('❌ Delete Session', f"delete_session_{session_index}".encode())],
                [Button.inline('🔙 Back to Session', f"manage_session_{session_index}".encode())],
                [Button.inline('🔙 Back to Main Menu', b'back_to_menu')]
            ],
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error verifying session: {e}")
        await msg.edit(
            f"❌ *Error verifying session*\n\n"
            f"An error occurred: {str(e)}",
            buttons=[
                [Button.inline('🔙 Back to Session', f"manage_session_{session_index}".encode())],
                [Button.inline('🔙 Back to Main Menu', b'back_to_menu')]
            ],
            parse_mode='Markdown'
        )

@bot.on(events.CallbackQuery(pattern=r"show_session_(\d+)"))
async def show_session(event):
    """Show the session string for a saved session"""
    user_id = event.sender_id
    session_index = int(event.data.decode().split('_')[-1])
    
    # Validate session index
    if user_id not in saved_sessions or session_index >= len(saved_sessions[user_id]):
        await event.edit(
            "❌ Session not found. It may have been deleted.",
            buttons=[[Button.inline('🔙 Back to Main Menu', b'back_to_menu')]]
        )
        return
    
    # Get session info
    session = saved_sessions[user_id][session_index]
    session_string = session.get('string', '')
    label = session.get('label', f"Session {session_index+1}")
    
    if not session_string:
        await event.edit(
            "❌ Invalid session data. Please generate a new session.",
            buttons=[[Button.inline('🔙 Back to Sessions', b'view_sessions')]]
        )
        return
    
    msg = await event.edit(
        f"🔐 *Session String for: {label}*\n\n"
        f"`{session_string}`\n\n"
        f"⚠️ *IMPORTANT*: This session string gives full access to your account. "
        f"Never share it with anyone!",
        buttons=[
            [Button.inline('🔙 Back to Session', f"manage_session_{session_index}".encode())],
            [Button.inline('🔙 Back to Main Menu', b'back_to_menu')]
        ],
        parse_mode='Markdown'
    )
    
    # Auto-delete for security if enabled
    if user_id in auto_delete_settings and auto_delete_settings[user_id]:
        # Schedule message deletion in 5 minutes
        asyncio.create_task(auto_delete_message(msg, 300))

@bot.on(events.CallbackQuery(pattern=r"edit_label_(\d+)"))
async def edit_label_request(event):
    """Request a new label for a session"""
    user_id = event.sender_id
    session_index = int(event.data.decode().split('_')[-1])
    
    # Validate session index
    if user_id not in saved_sessions or session_index >= len(saved_sessions[user_id]):
        await event.edit(
            "❌ Session not found. It may have been deleted.",
            buttons=[[Button.inline('🔙 Back to Main Menu', b'back_to_menu')]]
        )
        return
    
    # Get current label
    session = saved_sessions[user_id][session_index]
    label = session.get('label', f"Session {session_index+1}")
    
    # Set state to expect new label
    active_processes[user_id] = {
        'expecting': 'session_label',
        'session_index': session_index
    }
    
    await event.edit(
        f"✏️ *Edit Session Label* ✏️\n\n"
        f"Current label: *{label}*\n\n"
        f"Please send a new name for this session:",
        buttons=[[Button.inline('🔙 Cancel', f"manage_session_{session_index}".encode())]],
        parse_mode='Markdown'
    )

@bot.on(events.CallbackQuery(pattern=r"delete_session_(\d+)"))
async def delete_session_confirm(event):
    """Confirm deletion of a session"""
    user_id = event.sender_id
    session_index = int(event.data.decode().split('_')[-1])
    
    # Validate session index
    if user_id not in saved_sessions or session_index >= len(saved_sessions[user_id]):
        await event.edit(
            "❌ Session not found. It may have been deleted.",
            buttons=[[Button.inline('🔙 Back to Main Menu', b'back_to_menu')]]
        )
        return
    
    # Get label
    session = saved_sessions[user_id][session_index]
    label = session.get('label', f"Session {session_index+1}")
    
    # Show confirmation
    await event.edit(
        f"⚠️ *Delete Session* ⚠️\n\n"
        f"Are you sure you want to delete *{label}*?\n\n"
        f"This action cannot be undone.",
        buttons=[
            [Button.inline('✅ Yes, Delete Session', f"confirm_delete_{session_index}".encode())],
            [Button.inline('❌ No, Keep Session', f"manage_session_{session_index}".encode())]
        ],
        parse_mode='Markdown'
    )

@bot.on(events.CallbackQuery(pattern=r"confirm_delete_(\d+)"))
async def delete_session_confirmed(event):
    """Delete session after confirmation"""
    user_id = event.sender_id
    session_index = int(event.data.decode().split('_')[-1])
    
    # Validate session index
    if user_id not in saved_sessions or session_index >= len(saved_sessions[user_id]):
        await event.edit(
            "❌ Session not found. It may have been deleted.",
            buttons=[[Button.inline('🔙 Back to Main Menu', b'back_to_menu')]]
        )
        return
    
    # Get label before deletion
    label = saved_sessions[user_id][session_index].get('label', f"Session {session_index+1}")
    
    # Delete session
    del saved_sessions[user_id][session_index]
    
    # Clean up if no sessions left
    if not saved_sessions[user_id]:
        del saved_sessions[user_id]
    
    await event.edit(
        f"✅ *Session Deleted*\n\n"
        f"*{label}* has been deleted successfully.",
        buttons=[
            [Button.inline('🔙 Back to Sessions', b'view_sessions')],
            [Button.inline('🔙 Back to Main Menu', b'back_to_menu')]
        ],
        parse_mode='Markdown'
    )

@bot.on(events.CallbackQuery(data=b'check_session'))
async def check_session_request(event):
    """Request a session string to check its validity"""
    user_id = event.sender_id
    
    # Edit the button message to ask for the session string and save it
    msg = await event.edit(
        "🔍 *Check Session Validity* 🔍\n\n"
        "Please send the session string you want to check.\n\n"
        "This will verify if the session is still valid and show information about it.",
        buttons=[[Button.inline('🔙 Back to Main Menu', b'back_to_menu')]],
        parse_mode='Markdown'
    )
    
    # Set state to expect session string and save the status message
    active_processes[user_id] = {
        'expecting': 'session_string_to_check',
        'status_msg': msg  # Save the message to edit it later
    }

@bot.on(events.CallbackQuery(data=b'show_help'))
async def show_help(event):
    """Show help information"""
    markup = [[Button.inline('🔙 Back to Main Menu', b'back_to_menu')]]
    
    await event.edit(
        "❓ *Advanced Telethon Session Manager Help* ❓\n\n"
        "This bot helps you generate, validate, and manage Telethon session strings with an intuitive button-based interface.\n\n"
        "*Key Features:*\n"
        "• Button-based interface (no command memorization needed)\n"
        "• Generate multiple session strings for various accounts\n"
        "• Custom labeling for easy session identification\n"
        "• Session validation with detailed account information\n"
        "• Enhanced security with automatic data protection\n"
        "• Manage multiple sessions in one place\n\n"
        "*Enhanced Security Features:*\n"
        "• Phone numbers are automatically deleted from chat history\n"
        "• Verification codes are immediately removed after submission\n"
        "• 2FA passwords are deleted for maximum security\n"
        "• Session strings can be auto-deleted after viewing (configurable)\n"
        "• All security features designed to protect your account\n\n"
        "*Security Recommendations:*\n"
        "• Keep auto-deletion enabled for session strings\n"
        "• Always validate sessions before using them\n"
        "• Never share session strings with unauthorized parties\n"
        "• Use descriptive labels to identify sessions\n"
        "• Store session strings in a secure location\n\n"
        "*Usage Tips:*\n"
        "• Use the main menu to access all features\n"
        "• Follow the on-screen prompts for each action\n"
        "• Provide verification codes with or without spaces\n\n"
        "*Need more help?*\n"
        "If you have questions or need assistance, please contact the bot administrator.",
        buttons=markup,
        parse_mode='Markdown'
    )

@bot.on(events.NewMessage(pattern='/cancel'))
async def cancel_command(event):
    """Cancel the ongoing process"""
    user_id = event.sender_id
    
    if user_id in active_processes:
        # Clean up client if exists
        if 'client' in active_processes[user_id]:
            client = active_processes[user_id]['client']
            if client:
                try:
                    await client.disconnect()
                except:
                    pass
        # Remove user data
        del active_processes[user_id]
    
    # Create main menu with buttons
    markup = [
        [Button.inline('📱 Generate New Session', b'start_session')],
        [Button.inline('🔍 Check Session Validity', b'check_session')],
        [Button.inline('📋 View My Sessions', b'view_sessions')],
        [Button.inline('🔒 Auto-Delete Messages', b'toggle_autodelete')],
        [Button.inline('❓ Help', b'show_help')]
    ]
    
    await event.respond(
        "❌ Process cancelled.\n\n"
        "What would you like to do next? Choose an option from the menu below:",
        buttons=markup,
        parse_mode='Markdown'
    )

def main():
    """Start the bot"""
    print("Starting Advanced Telethon Session Manager...")
    
    bot.start(bot_token=BOT_TOKEN)
    print("Advanced Telethon Session Manager started successfully!")
    print("Enhanced security features enabled.")
    print("Press Ctrl+C to stop.")
    
    # Run the bot until disconnected
    bot.run_until_disconnected()

if __name__ == "__main__":
    main()