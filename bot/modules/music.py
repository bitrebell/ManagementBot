import os
import re
import time
import asyncio
import aiohttp
import aiofiles
import yt_dlp
from collections import deque
from typing import Dict, List, Union, Optional

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant, ChatAdminRequired

from bot.utils import is_admin, is_bot_admin

# Module info
__MODULE__ = "Music"
__HELP__ = """
**Music Module:**

/play [song name or YouTube URL] - Play a song in voice chat
/skip - Skip the current song
/pause - Pause the current song
/resume - Resume playback
/stop - Stop playback and clear queue
/queue - Show the current queue
/now - Show the currently playing song
/volume [1-200] - Set the volume (admins only)

The bot must be an admin in the group to play music.
"""

# Music queues for each chat
music_queue: Dict[int, deque] = {}
current_song: Dict[int, Dict] = {}
active_chats: Dict[int, Dict] = {}

# YouTube regex pattern
YOUTUBE_REGEX = r"(?:youtube\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu\.be/)([^\"&?/ ]{11})"

# Download directory
DOWNLOAD_DIR = "bot/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# YT-DLP options
ydl_opts = {
    "format": "bestaudio/best",
    "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s",
    "geo_bypass": True,
    "nocheckcertificate": True,
    "quiet": True,
    "no_warnings": True,
    "prefer_ffmpeg": True,
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192",
    }],
}

# Helper function to extract video ID from URL
def extract_youtube_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from URL"""
    match = re.search(YOUTUBE_REGEX, url)
    if match:
        return match.group(1)
    return None

# Helper function to search for songs
async def search_song(query: str) -> Optional[Dict]:
    """Search for a song on YouTube"""
    if extract_youtube_id(query):
        # If query is a YouTube URL, use it directly
        video_id = extract_youtube_id(query)
        url = f"https://www.youtube.com/watch?v={video_id}"
    else:
        # Otherwise, search for the song
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "default_search": "ytsearch1"}) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch1:{query}", download=False)
                if not info or "entries" not in info or not info["entries"]:
                    return None
                url = info["entries"][0]["webpage_url"]
            except Exception as e:
                print(f"Error searching for song: {str(e)}")
                return None
    
    # Get video info
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return {
                "id": info["id"],
                "title": info["title"],
                "url": url,
                "duration": info["duration"],
                "thumbnail": info.get("thumbnail", ""),
                "uploader": info.get("uploader", "Unknown")
            }
        except Exception as e:
            print(f"Error getting video info: {str(e)}")
            return None

# Helper function to download song
async def download_song(song_info: Dict) -> Optional[str]:
    """Download a song from YouTube"""
    video_id = song_info["id"]
    file_path = f"{DOWNLOAD_DIR}/{video_id}.mp3"
    
    # Check if file already exists
    if os.path.exists(file_path):
        return file_path
    
    # Download the song
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([song_info["url"]])
        return file_path
    except Exception as e:
        print(f"Error downloading song: {str(e)}")
        return None

# Helper function to format duration
def format_duration(seconds: int) -> str:
    """Format duration in seconds to MM:SS format"""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"

# Play command handler
@Client.on_message(filters.command("play") & filters.group)
async def play_song(client: Client, message: Message):
    """Play a song in voice chat"""
    chat_id = message.chat.id
    
    # Check if the bot is admin
    if not await is_bot_admin(message):
        await message.reply_text("I need to be an admin to play music!")
        return
    
    # Check if command has arguments
    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply_text("Please provide a song name or YouTube URL!")
        return
    
    # Get query
    if message.reply_to_message and message.reply_to_message.text:
        query = message.reply_to_message.text
    else:
        query = message.text.split(None, 1)[1]
    
    # Send searching message
    search_msg = await message.reply_text("🔍 Searching...")
    
    # Search for the song
    song_info = await search_song(query)
    if not song_info:
        await search_msg.edit_text("❌ Song not found!")
        return
    
    # Initialize queue if not exists
    if chat_id not in music_queue:
        music_queue[chat_id] = deque()
    
    # Add song to queue
    music_queue[chat_id].append(song_info)
    
    # Create song info message
    duration = format_duration(song_info["duration"])
    song_text = f"🎵 Added to queue:\n\n"
    song_text += f"**Title:** {song_info['title']}\n"
    song_text += f"**Duration:** {duration}\n"
    song_text += f"**Requested by:** {message.from_user.mention}\n"
    
    # Create keyboard with song URL
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Watch on YouTube", url=song_info["url"])]]
    )
    
    # Edit search message with song info
    await search_msg.edit_text(song_text, reply_markup=keyboard)
    
    # Start playing if not already playing
    if chat_id not in active_chats:
        await start_playing(client, chat_id)

# Helper function to start playing
async def start_playing(client: Client, chat_id: int):
    """Start playing songs from the queue"""
    # Check if queue is empty
    if not music_queue[chat_id]:
        return
    
    # Get next song from queue
    song_info = music_queue[chat_id].popleft()
    current_song[chat_id] = song_info
    
    # Download the song
    file_path = await download_song(song_info)
    if not file_path:
        await client.send_message(chat_id, "❌ Failed to download song!")
        # Try next song
        if music_queue[chat_id]:
            await start_playing(client, chat_id)
        return
    
    # Join voice chat and play song
    try:
        # Mark chat as active
        active_chats[chat_id] = {"playing": True, "paused": False}
        
        # Create song info message
        duration = format_duration(song_info["duration"])
        song_text = f"🎵 Now playing:\n\n"
        song_text += f"**Title:** {song_info['title']}\n"
        song_text += f"**Duration:** {duration}\n"
        song_text += f"**Uploader:** {song_info['uploader']}\n"
        
        # Create keyboard with song URL
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Watch on YouTube", url=song_info["url"])]]
        )
        
        # Send now playing message
        await client.send_message(chat_id, song_text, reply_markup=keyboard)
        
        # TODO: Implement actual voice chat playback using Pyrogram's methods
        # This is a placeholder for the actual implementation
        # In a real implementation, you would use Pyrogram's methods to join voice chat and play audio
        
        # Simulate song duration
        await asyncio.sleep(song_info["duration"])
        
        # Play next song if available
        if music_queue[chat_id]:
            await start_playing(client, chat_id)
        else:
            # No more songs in queue
            if chat_id in active_chats:
                del active_chats[chat_id]
            if chat_id in current_song:
                del current_song[chat_id]
            await client.send_message(chat_id, "✅ Queue finished!")
    
    except Exception as e:
        print(f"Error playing song: {str(e)}")
        await client.send_message(chat_id, f"❌ Error playing song: {str(e)}")
        
        # Try next song
        if music_queue[chat_id]:
            await start_playing(client, chat_id)
        else:
            # No more songs in queue
            if chat_id in active_chats:
                del active_chats[chat_id]
            if chat_id in current_song:
                del current_song[chat_id]

# Skip command handler
@Client.on_message(filters.command("skip") & filters.group)
async def skip_song(client: Client, message: Message):
    """Skip the current song"""
    chat_id = message.chat.id
    
    # Check if music is playing
    if chat_id not in active_chats:
        await message.reply_text("❌ No song is currently playing!")
        return
    
    # Check if user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to skip songs!")
        return
    
    # Skip current song
    await message.reply_text("⏭️ Skipped the current song!")
    
    # Play next song if available
    if music_queue[chat_id]:
        await start_playing(client, chat_id)
    else:
        # No more songs in queue
        if chat_id in active_chats:
            del active_chats[chat_id]
        if chat_id in current_song:
            del current_song[chat_id]
        await message.reply_text("✅ Queue finished!")

# Pause command handler
@Client.on_message(filters.command("pause") & filters.group)
async def pause_song(client: Client, message: Message):
    """Pause the current song"""
    chat_id = message.chat.id
    
    # Check if music is playing
    if chat_id not in active_chats:
        await message.reply_text("❌ No song is currently playing!")
        return
    
    # Check if already paused
    if active_chats[chat_id]["paused"]:
        await message.reply_text("⚠️ Music is already paused!")
        return
    
    # Check if user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to pause songs!")
        return
    
    # Pause the song
    active_chats[chat_id]["paused"] = True
    
    # TODO: Implement actual pause functionality
    # This is a placeholder for the actual implementation
    
    await message.reply_text("⏸️ Paused the current song!")

# Resume command handler
@Client.on_message(filters.command("resume") & filters.group)
async def resume_song(client: Client, message: Message):
    """Resume the current song"""
    chat_id = message.chat.id
    
    # Check if music is playing
    if chat_id not in active_chats:
        await message.reply_text("❌ No song is currently playing!")
        return
    
    # Check if not paused
    if not active_chats[chat_id]["paused"]:
        await message.reply_text("⚠️ Music is already playing!")
        return
    
    # Check if user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to resume songs!")
        return
    
    # Resume the song
    active_chats[chat_id]["paused"] = False
    
    # TODO: Implement actual resume functionality
    # This is a placeholder for the actual implementation
    
    await message.reply_text("▶️ Resumed the current song!")

# Stop command handler
@Client.on_message(filters.command("stop") & filters.group)
async def stop_song(client: Client, message: Message):
    """Stop playback and clear queue"""
    chat_id = message.chat.id
    
    # Check if music is playing
    if chat_id not in active_chats:
        await message.reply_text("❌ No song is currently playing!")
        return
    
    # Check if user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to stop playback!")
        return
    
    # Clear queue and stop playback
    if chat_id in music_queue:
        music_queue[chat_id].clear()
    
    if chat_id in active_chats:
        del active_chats[chat_id]
    
    if chat_id in current_song:
        del current_song[chat_id]
    
    # TODO: Implement actual stop functionality
    # This is a placeholder for the actual implementation
    
    await message.reply_text("⏹️ Stopped playback and cleared queue!")

# Queue command handler
@Client.on_message(filters.command("queue") & filters.group)
async def show_queue(client: Client, message: Message):
    """Show the current queue"""
    chat_id = message.chat.id
    
    # Check if queue exists
    if chat_id not in music_queue or not music_queue[chat_id]:
        if chat_id in current_song:
            # Only current song is playing
            song_info = current_song[chat_id]
            duration = format_duration(song_info["duration"])
            
            queue_text = f"🎵 **Now Playing:**\n"
            queue_text += f"1. {song_info['title']} ({duration})\n\n"
            queue_text += "No songs in queue."
            
            await message.reply_text(queue_text)
        else:
            await message.reply_text("❌ No songs in queue!")
        return
    
    # Create queue message
    queue_text = "🎵 **Music Queue:**\n\n"
    
    # Add current song if playing
    if chat_id in current_song:
        song_info = current_song[chat_id]
        duration = format_duration(song_info["duration"])
        queue_text += f"**Now Playing:**\n"
        queue_text += f"• {song_info['title']} ({duration})\n\n"
    
    # Add queued songs
    queue_text += "**Up Next:**\n"
    for i, song_info in enumerate(music_queue[chat_id], 1):
        duration = format_duration(song_info["duration"])
        queue_text += f"{i}. {song_info['title']} ({duration})\n"
    
    await message.reply_text(queue_text)

# Now playing command handler
@Client.on_message(filters.command("now") & filters.group)
async def now_playing(client: Client, message: Message):
    """Show the currently playing song"""
    chat_id = message.chat.id
    
    # Check if a song is playing
    if chat_id not in current_song:
        await message.reply_text("❌ No song is currently playing!")
        return
    
    # Get current song info
    song_info = current_song[chat_id]
    duration = format_duration(song_info["duration"])
    
    # Create song info message
    song_text = f"🎵 Now playing:\n\n"
    song_text += f"**Title:** {song_info['title']}\n"
    song_text += f"**Duration:** {duration}\n"
    song_text += f"**Uploader:** {song_info['uploader']}\n"
    
    # Create keyboard with song URL
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Watch on YouTube", url=song_info["url"])]]
    )
    
    await message.reply_text(song_text, reply_markup=keyboard)

# Volume command handler
@Client.on_message(filters.command("volume") & filters.group)
async def set_volume(client: Client, message: Message):
    """Set the volume"""
    chat_id = message.chat.id
    
    # Check if music is playing
    if chat_id not in active_chats:
        await message.reply_text("❌ No song is currently playing!")
        return
    
    # Check if user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to change the volume!")
        return
    
    # Check if command has arguments
    if len(message.command) < 2:
        await message.reply_text("Please provide a volume level between 1 and 200!")
        return
    
    # Try to parse the volume
    try:
        volume = int(message.command[1])
        if volume < 1 or volume > 200:
            await message.reply_text("Volume must be between 1 and 200!")
            return
        
        # TODO: Implement actual volume control
        # This is a placeholder for the actual implementation
        
        await message.reply_text(f"🔊 Volume set to {volume}%!")
    except ValueError:
        await message.reply_text("Please provide a valid number for the volume!") 