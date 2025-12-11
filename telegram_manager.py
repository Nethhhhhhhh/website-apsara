from telethon import TelegramClient, events
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest, CheckChatInviteRequest
from telethon.tl.types import InputPeerUser
from telethon.errors import PhoneNumberInvalidError, PeerFloodError, UserPrivacyRestrictedError, FloodWaitError, UserAlreadyParticipantError
import os
import csv
import asyncio
import random
import config
import traceback

class TelegramManager:
    def __init__(self):
        # Default to Config if available, else None
        self.api_id = config.API_ID
        self.api_hash = config.API_HASH
        self.phone = config.PHONE
        self.session_name = config.SESSION_NAME
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        
        # Initialize Bot Client
        if config.BOT_TOKEN and config.BOT_TOKEN.lower() not in ['your_bot_token', 'none', '']:
            try:
                self.bot = TelegramClient('apsara_bot', self.api_id, self.api_hash)
                # We must start the bot, but not in __init__ as it returns a coroutine.
                # We will start it in the connect method or separate init method.
                # For now, we just attach handlers.
                self.setup_handlers()
                # We can start it lazily or create a task if loop assumes running.
                # In separate method: self.bot.start(bot_token=config.BOT_TOKEN)
            except Exception as e:
                print(f"Stats: Failed to start Bot Client: {e}")
                self.bot = None
        else:
            self.bot = None

    async def update_session(self, api_id, api_hash, phone):
        """Updates the client with new credentials and attempts to connect."""
        if self.client:
            await self.client.disconnect()
            
        self.api_id = int(api_id)
        self.api_hash = api_hash
        self.phone = phone
        
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        await self.client.connect()
        return True

    def setup_handlers(self):
        if not self.bot:
            return

        @self.bot.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            sender = await event.get_sender()
            first_name = sender.first_name if sender else "User"
            
            # Check for payload (e.g. /start login)
            payload = event.raw_text.split()
            if len(payload) > 1 and payload[1] == 'login':
                await event.respond(f"👋 **Welcome back, {first_name}!**\n\nYou have accessed the Quick Login flow.\nPlease return to the website and enter your phone number to receive your OTP code here.")
            else:
                await event.respond(f"Hello {first_name}! I am the Apsara Helper Bot.\n\nI can help you manage your channel and download videos.")

    async def connect(self):
        await self.client.connect()
        # Bot is auto-started in init via .start(), but we can ensure it's running if needed, 
        # though .start() returns the client and runs it. 
        # For Telethon bot client, typically we run_until_disconnected in main, 
        # but here we are in a FastAPI app. 
        # We rely on the event loop. .start() usually creates the task.
        if self.bot:
            await self.bot.start(bot_token=config.BOT_TOKEN)
        
    async def is_authorized(self):
        return await self.client.is_user_authorized()
        
    async def send_code(self, phone):
        self.phone = phone
        await self.client.connect()
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(phone)
            return True
        return False # Already authorized
    
    async def sign_in(self, code):
        await self.client.connect()
        try:
            await self.client.sign_in(self.phone, code)
            return True, "Login successful"
        except Exception as e:
            return False, str(e)

    async def scrape_members(self, target_group):
        try:
            authorized = await self.client.is_user_authorized()
        except Exception as e:
            yield f"Error checking authorization: {e}"
            return

        if not authorized:
            yield "Not authorized. Please login first."
            return
            
        try:
            target = target_group.strip()
            yield f"Resolving target: {target}..."
            
            # Handle full URLs: https://t.me/username/123 or https://t.me/username
            if "t.me/" in target:
                import re
                
                # Check for Private Invite Link: t.me/+HASH or t.me/joinchat/HASH
                invite_match = re.search(r"t\.me/(\+|joinchat/)([\w-]+)", target)
                if invite_match:
                    invite_hash = invite_match.group(2)
                    yield f"Detected invite link with hash: {invite_hash}"
                    
                    # Strategy 1: Check Invite (Most reliable for getting entity)
                    try:
                        invite_prop = await self.client(CheckChatInviteRequest(invite_hash))
                        
                        if hasattr(invite_prop, 'chat') and invite_prop.chat:
                            target = invite_prop.chat
                        elif hasattr(invite_prop, 'channel') and invite_prop.channel:
                             target = invite_prop.channel
                        yield "Resolved via CheckChatInviteRequest."
                    except Exception as e:
                        print(f"CheckChatInviteRequest failed: {e}")
                        yield f"CheckChatInviteRequest failed: {e}"

                    # Strategy 2: If we didn't get target from Check (rare), try Join and get from Updates
                    if isinstance(target, str): # Still a string means Strategy 1 failed to set entity
                        try:
                            yield "Attempting to join via ImportChatInviteRequest..."
                            updates = await self.client(ImportChatInviteRequest(invite_hash))
                            if hasattr(updates, 'chats') and updates.chats:
                                target = updates.chats[0]
                            yield "Joined and resolved channel."
                        except UserAlreadyParticipantError:
                            yield "Already a participant, limiting resolution options."
                            # We are already in, but Check failed? Weird.
                            # Fallback: Try to find in dialogs? Or assumes the user provided a link we can't resolving.
                            # But usually Check works even if joined.
                            pass
                        except Exception as e:
                            print(f"ImportChatInviteRequest failed: {e}")
                            yield f"ImportChatInviteRequest failed: {e}"
            
            yield f"Fetching participants from {target}..."
            # Now fetch participants
            all_participants = []
            try:
                # Use iter_participants for better handling of large groups
                async for user in self.client.iter_participants(target, aggressive=True):
                    all_participants.append(user)
                    if len(all_participants) % 100 == 0:
                        yield f"Scraped {len(all_participants)} members so far..."
            except Exception as e:
                yield f"Error fetching participants: {e}"
                if not all_participants:
                     return

            filename = "data.csv"
            yield f"Writing {len(all_participants)} members to {filename}..."
            
            with open(filename, "w", encoding='UTF-8', newline='') as f:
                writer = csv.writer(f, delimiter=",", lineterminator="\n")
                writer.writerow(['sr. no.', 'username', 'user id', 'access_hash', 'name', 'Status']) # Header
                
                for i, user in enumerate(all_participants, start=1):
                    username = user.username if user.username else ""
                    first_name = user.first_name if user.first_name else ""
                    last_name = user.last_name if user.last_name else ""
                    name = (first_name + ' ' + last_name).strip()
                    access_hash = getattr(user, 'access_hash', '')
                    
                    writer.writerow([i, username, user.id, access_hash, name, 'seen'])
            
            yield f"Successfully scraped {len(all_participants)} members to {filename}."
        except Exception as e:
            traceback.print_exc()
            yield f"Error scraping: {str(e)}"

    async def add_members(self, target_channel, start_index=1, end_index=50, auto_run=False):
        try:
            authorized = await self.client.is_user_authorized()
        except Exception as e:
            yield f"Error checking authorization: {e}"
            return

        if not authorized:
            yield "Not authorized. Please login first."
            return
            
        input_file = 'data.csv'
        if not os.path.exists(input_file):
            yield "data.csv not found. Please run Member Scraper first."
            return
            
        users = []
        try:
            with open(input_file, encoding='UTF-8') as f:
                rows = csv.reader(f, delimiter=",", lineterminator="\n")
                next(rows, None) # Skip header
                for row in rows:
                    user = {}
                    user['srno'] = row[0]
                    user['username'] = row[1]
                    user['id'] = int(row[2])
                    # Handle new csv format with access_hash
                    if len(row) > 5:
                        user['access_hash'] = row[3]
                        user['name'] = row[4]
                    else:
                        # Old format support
                        user['access_hash'] = None
                        user['name'] = row[3]
                    users.append(user)
        except Exception as e:
            yield f"Error reading CSV: {str(e)}"
            return

        yield f"Loaded {len(users)} users. Starting add process..."
        n = 0
        
        # User logic loop
        for user in users:
            try:
                user_srno = int(user['srno'])
                if start_index <= user_srno <= end_index:
                    n += 1
                    # User logic: sleep every 50k
                    if n % 50000 == 0:
                        yield "Added 50000 members, sleeping for 900 seconds..."
                        await asyncio.sleep(900)
                    
                    try:
                        user_to_add = user['username']
                        if not user['username']:
                            # "No username, use ID + AccessHash"
                            if user.get('access_hash'):
                                try:
                                    user_to_add = InputPeerUser(user['id'], int(user['access_hash']))
                                except Exception:
                                     # If hash is invalid string
                                     user_to_add = user['id']
                            else:
                                user_to_add = user['id']
                        
                        yield f"Adding {user['id']} (Username: {user['username'] or 'None'})"
                        
                        await self.client(InviteToChannelRequest(
                            target_channel,
                            [user_to_add]
                        ))
                        
                        # User requested safer wait time (15-180s) to avoid errors
                        wait_seconds = random.randint(15, 180)
                        yield f"Waiting {wait_seconds}s..."
                        await asyncio.sleep(wait_seconds) 
                        
                    except (PeerFloodError, FloodWaitError) as e:
                        if auto_run:
                            wait_flood = random.randint(30, 180)
                            
                            req_seconds = getattr(e, 'seconds', 0)
                            if req_seconds and req_seconds > 0:
                                pass

                            yield f"Flood Error ({getattr(e, 'seconds', 'unknown')}s)! Auto-Run Active. Waiting {wait_flood} seconds..."
                            await asyncio.sleep(wait_flood)
                            continue
                        else:
                            yield f"Getting Flood Error ({getattr(e, 'seconds', 'unknown')}s). Script is stopping now."
                            break
                    except UserPrivacyRestrictedError:
                         yield f"User {user['id']} has privacy restricted. Skipping."
                    except Exception as e:
                        # traceback.print_exc()
                        yield f"Unexpected Error adding {user['id']}: {str(e)}"
                        continue
                elif user_srno > end_index:
                    yield "Reached end index."
                    break
            except ValueError:
                continue

        yield "Process Completed."

    async def download_video(self, link):
        print(f"DEBUG: Attempting to download from link: {link}")
        try:
            authorized = await self.client.is_user_authorized()
        except Exception as e:
            print(f"DEBUG: Error checking authorization: {e}")
            return {"status": "error", "message": f"Connection Error: {e}"}

        if not authorized:
            print("DEBUG: User not authorized")
            return {"status": "error", "message": "Not authorized. Please login first."}

        import re
        try:
            link = link.strip()
            # Handle Private Links: t.me/c/123456789/123
            if "t.me/c/" in link:
                print("DEBUG: Detected PRIVATE link format")
                match = re.search(r"t\.me/c/(\d+)/(\d+)", link)
                if not match:
                    print("DEBUG: Invalid private link regex match")
                    return {"status": "error", "message": "Invalid private link format."}
                
                chat_id_num = int(match.group(1))
                msg_id = int(match.group(2))
                print(f"DEBUG: Private Chat ID: {chat_id_num}, Msg ID: {msg_id}")
                
                # Resolving Peer
                # Telethon often requires the -100 prefix for channel IDs
                peer_id = int(f"-100{chat_id_num}")
                print(f"DEBUG: Trying to get entity for peer_id: {peer_id}")
                
                try:
                    entity = await self.client.get_entity(peer_id)
                except ValueError:
                    # If failed, try without -100 (unlikely for supergroups but possible for some chats)
                    print(f"DEBUG: Failed with -100, trying raw ID: {chat_id_num}")
                    try:
                        entity = await self.client.get_entity(chat_id_num)
                    except Exception as e:
                        print(f"DEBUG: Could not resolve private entity: {e}")
                        return {"status": "error", "message": f"Could not resolve private channel. Are you a member? {e}"}

            # Handle Public Links: t.me/username/123
            else:
                print("DEBUG: Detected PUBLIC link format")
                match = re.search(r"t\.me/([^/]+)/(\d+)", link)
                if not match:
                    print("DEBUG: Invalid public link regex match")
                    return {"status": "error", "message": "Invalid public link format."}
                
                username = match.group(1)
                msg_id = int(match.group(2))
                print(f"DEBUG: Username: {username}, Msg ID: {msg_id}")
                
                try:
                    entity = await self.client.get_entity(username)
                except Exception as e:
                     print(f"DEBUG: Could not resolve public entity: {e}")
                     return {"status": "error", "message": f"Could not find public channel '{username}'."}

            print("DEBUG: Entity resolved. Fetching message...")
            message = await self.client.get_messages(entity, ids=msg_id)

            if not message:
                 print("DEBUG: Message not found (None returned)")
                 return {"status": "error", "message": "Message not found."}
            
            if not message.media:
                print("DEBUG: Message found but has NO media")
                return {"status": "error", "message": "Message contains no media."}

            print(f"DEBUG: Message has media: {message.media.__class__.__name__}. Downloading...")

            # Define path
            download_dir = os.path.join("static", "downloads")
            os.makedirs(download_dir, exist_ok=True)
            
            def progress_callback(current, total):
                print(f"Download Progress: {current * 100 / total:.1f}%")

            file_path = await self.client.download_media(
                message, 
                file=download_dir,
                progress_callback=progress_callback
            )
            print(f"DEBUG: Download finished at {file_path}")
            
            # Return relative path for frontend
            rel_path = os.path.relpath(file_path, start=os.getcwd()).replace("\\", "/")
            if not rel_path.startswith("static"):
                 rel_path = f"/static/downloads/{os.path.basename(file_path)}"
            else:
                rel_path = "/" + rel_path 
                
            return {"status": "success", "file_path": rel_path, "message": "Download successful!"}

        except Exception as e:
            traceback.print_exc()
            print(f"DEBUG: Exception in download_video: {e}")
            return {"status": "error", "message": f"Download failed: {str(e)}"}

# Global Instance
telegram_bot = TelegramManager()
