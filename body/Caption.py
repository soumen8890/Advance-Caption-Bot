import os
import sys
import re
import asyncio
from time import time
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import errors
from info import *
from Script import script
from .database import *

# Helper functions
def get_size(size):
    """Convert file size to human-readable format"""
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units) - 1:
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def get_wish():
    """Return appropriate greeting based on time of day"""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Good Morning"
    elif 12 <= hour < 16:
        return "Good Afternoon"
    elif 16 <= hour < 20:
        return "Good Evening"
    return "Good Night"

def extract_metadata(file_name, default_caption, file_attr=None):
    """Extract all metadata from filename and caption"""
    metadata = {
        'filename': re.sub(r"@\w+\s*", "", file_name).replace("_", " ").replace(".", " "),
        'filesize': None,
        'caption': default_caption or "",
        'language': 'Hindi-English',
        'year': None,
        'quality': None,
        'season': None,
        'episode': None,
        'duration': None,
        'height': None,
        'width': None,
        'ext': file_name.split('.')[-1].upper() if '.' in file_name else '',
        'resolution': None,
        'mime_type': None,
        'title': None,
        'artist': None,
        'wish': get_wish()
    }
    
    # File size
    if file_attr and hasattr(file_attr, 'file_size'):
        metadata['filesize'] = get_size(file_attr.file_size)
    
    # Language extraction
    language_pattern = r'\b(Hindi|English|Tamil|Telugu|Malayalam|Kannada|Hin|Tel|Tam|Mal)\b'
    languages = set(re.findall(language_pattern, file_name + " " + default_caption, re.IGNORECASE))
    if languages:
        metadata['language'] = ", ".join(sorted(languages, key=str.lower))
    
    # Year extraction
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', file_name + " " + default_caption)
    if year_match:
        metadata['year'] = year_match.group(1)
    
    # Quality extraction
    quality_match = re.search(r'\b(360p|480p|720p|1080p|1440p|2160p|4K|8K|HD|FHD|UHD)\b', file_name, re.IGNORECASE)
    if quality_match:
        metadata['quality'] = quality_match.group(0)
    
    # Season-Episode extraction
    season_ep_match = re.search(r'\bS(\d{1,2})E(\d{1,2})\b', file_name, re.IGNORECASE)
    if season_ep_match:
        metadata['season'] = season_ep_match.group(1)
        metadata['episode'] = season_ep_match.group(2)
    
    # Video specific attributes
    if file_attr and hasattr(file_attr, 'duration'):
        metadata['duration'] = str(file_attr.duration) + "s"
    
    if file_attr and hasattr(file_attr, 'height') and hasattr(file_attr, 'width'):
        metadata['height'] = file_attr.height
        metadata['width'] = file_attr.width
        metadata['resolution'] = f"{file_attr.width}x{file_attr.height}"
    
    if file_attr and hasattr(file_attr, 'mime_type'):
        metadata['mime_type'] = file_attr.mime_type
    
    # Audio specific attributes
    if file_attr and hasattr(file_attr, 'title'):
        metadata['title'] = file_attr.title
    
    if file_attr and hasattr(file_attr, 'performer'):
        metadata['artist'] = file_attr.performer
    
    return metadata

@Client.on_message(filters.command("start") & filters.private)
async def start_command(bot, message):
    user_id = message.from_user.id
    await insert(user_id)
    
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("➕️ Add Me To Your Channel ➕️", 
                url=f"https://t.me/{bot.username}?startchannel=true")
            ],[
                InlineKeyboardButton("Help", callback_data="help"),
                InlineKeyboardButton("About", callback_data="about")
            ],[
                InlineKeyboardButton("🌐 Update", url=UPDATE_CHANNEL),
                InlineKeyboardButton("📜 Support", url=SUPPORT_GROUP)
            ]
        ]
    )
    
    await message.reply_photo(
        photo=SILICON_PIC,
        caption=script.START_MESSAGE.format(message.from_user.mention),
        reply_markup=keyboard
    )

@Client.on_message(filters.private & filters.user(ADMIN) & filters.command("total_users"))
async def total_users_command(client, message):
    silicon = await message.reply_text("Please Wait...")
    total = await total_user()
    await silicon.edit(f"Total Users: `{total}`")

@Client.on_message(filters.private & filters.user(ADMIN) & filters.command("broadcast"))
async def broadcast_command(bot, message):
    if not message.reply_to_message:
        return await message.reply("Please reply to a message to broadcast")
    
    silicon = await message.reply_text("Getting all users from database...")
    all_users = await getid()
    total = await total_user()
    
    success = failed = deactivated = blocked = 0
    await silicon.edit("Broadcasting started...")
    
    async for user in all_users:
        try:
            await asyncio.sleep(1)  # Non-blocking sleep
            await message.reply_to_message.copy(user['_id'])
            success += 1
        except errors.InputUserDeactivated:
            deactivated += 1
            await delete({"_id": user['_id']})
        except errors.UserIsBlocked:
            blocked += 1
            await delete({"_id": user['_id']})
        except Exception as e:
            failed += 1
            await delete({"_id": user['_id']})
        
        try:
            if success % 10 == 0:  # Update progress every 10 messages
                await silicon.edit(
                    f"<u>Broadcast Progress</u>\n\n"
                    f"• Total users: {total}\n"
                    f"• Successful: {success}\n"
                    f"• Blocked users: {blocked}\n"
                    f"• Deleted accounts: {deactivated}\n"
                    f"• Unsuccessful: {failed}"
                )
        except FloodWait as e:
            await asyncio.sleep(e.value)
    
    await silicon.edit(
        f"<u>Broadcast Completed</u>\n\n"
        f"• Total users: {total}\n"
        f"• Successful: {success}\n"
        f"• Blocked users: {blocked}\n"
        f"• Deleted accounts: {deactivated}\n"
        f"• Unsuccessful: {failed}"
    )

@Client.on_message(filters.private & filters.user(ADMIN) & filters.command("restart"))
async def restart_command(bot, message):
    msg = await message.reply("**🔄 Processes Stopped. Bot is Restarting...**")
    await asyncio.sleep(3)
    await msg.edit("**✅ Bot is Restarted. Now you can use me**")
    os.execl(sys.executable, sys.executable, *sys.argv)

@Client.on_message(filters.command("set_cap") & filters.channel)
async def set_caption_command(bot, message):
    if len(message.command) < 2:
        return await message.reply(
            "Usage: /set_cap Your Caption\n\n"
            "Available variables:\n"
            "• {filename} - File name\n"
            "• {filesize} - File size\n"
            "• {caption} - Original caption\n"
            "• {language} - Detected languages\n"
            "• {year} - Detected year\n"
            "• {quality} - Video quality\n"
            "• {season} - Season number\n"
            "• {episode} - Episode number\n"
            "• {duration} - Duration (videos)\n"
            "• {height} - Video height\n"
            "• {width} - Video width\n"
            "• {ext} - File extension\n"
            "• {resolution} - Video resolution\n"
            "• {mime_type} - File mime type\n"
            "• {title} - Audio title\n"
            "• {artist} - Audio artist\n"
            "• {wish} - Time-based greeting"
        )
    
    chnl_id = message.chat.id
    caption = message.text.split(" ", 1)[1]
    
    chk_data = await chnl_ids.find_one({"chnl_id": chnl_id})
    if chk_data:
        await updateCap(chnl_id, caption)
        await message.reply(f"✅ Caption updated:\n\n{caption}")
    else:
        await addCap(chnl_id, caption)
        await message.reply(f"✅ New caption set:\n\n{caption}")

@Client.on_message(filters.command("del_cap") & filters.channel)
async def delete_caption_command(_, message):
    chnl_id = message.chat.id
    try:
        await chnl_ids.delete_one({"chnl_id": chnl_id})
        await message.reply("✅ Caption deleted. Now using default caption.")
    except Exception as e:
        error_msg = await message.reply(f"❌ Error: {e}")
        await asyncio.sleep(5)
        await error_msg.delete()

@Client.on_message(filters.channel)
async def handle_channel_messages(bot, message):
    if not message.media:
        return
    
    chnl_id = message.chat.id
    default_caption = message.caption or ""
    
    # Get file attributes
    file_attr = None
    for file_type in ("video", "audio", "document", "voice", "photo"):
        if getattr(message, file_type, None):
            file_attr = getattr(message, file_type)
            break
    
    if not file_attr or not hasattr(file_attr, "file_name"):
        return
    
    # Prepare metadata
    metadata = extract_metadata(file_attr.file_name, default_caption, file_attr)
    
    # Get custom caption if exists
    cap_dets = await chnl_ids.find_one({"chnl_id": chnl_id})
    caption_template = cap_dets["caption"] if cap_dets else DEF_CAP
    
    try:
        # Format caption with all available variables
        formatted_caption = caption_template.format(**metadata)
        await message.edit(formatted_caption)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.edit(formatted_caption)
    except Exception as e:
        print(f"Error editing caption: {e}")

# Callback handlers
@Client.on_callback_query(filters.regex(r'^start'))
async def callback_start(bot, query):
    await query.message.edit_text(
        text=script.START_TXT.format(query.from_user.mention),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("➕️ Add Me To Your Channel ➕️", 
                    url=f"https://t.me/{bot.username}?startchannel=true")
                ],
                [
                    InlineKeyboardButton("Help", callback_data="help"),
                    InlineKeyboardButton("About", callback_data="about")
                ],
                [
                    InlineKeyboardButton("🌐 Update", url=UPDATE_CHANNEL),
                    InlineKeyboardButton("📜 Support", url=SUPPORT_GROUP)
                ]
            ]
        ),
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex(r'^help'))
async def callback_help(bot, query):
    await query.message.edit_text(
        text=script.HELP_TXT,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("About", callback_data="about")],
                [InlineKeyboardButton("↩ Back", callback_data="start")]
            ]
        ),
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex(r'^about'))
async def callback_about(bot, query):
    await query.message.edit_text(
        text=script.ABOUT_TXT,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("How to Use Me ❓", callback_data="help")],
                [InlineKeyboardButton("↩ Back", callback_data="start")]
            ]
        ),
        disable_web_page_preview=True
    )
