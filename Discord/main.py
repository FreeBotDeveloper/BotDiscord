import discord
from discord.ext import commands, tasks
import feedparser
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()  # โหลดตัวแปรจาก .env

TOKEN = os.getenv("DISCORD_TOKEN")  # 👈 ดึง Token จาก .env

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
CONFIG_FILE = "config.json"

# ✅ โหลดข้อมูลเก่า
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# ✅ เซฟข้อมูล
def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# 🧠 โหลด config ไว้ในหน่วยความจำ
announcement_configs = load_config()

@bot.event
async def on_ready():
    print(f"✅ บอทออนไลน์แล้วในชื่อ: {bot.user}")
    check_youtube.start()

# ✅ /announcement [youtube_url]
@bot.slash_command(name="announcement", description="ตั้งค่าช่อง YouTube ที่จะแจ้งเตือนคลิปใหม่")
async def announcement(ctx, youtube_url: str):
    await ctx.defer()

    match = re.search(r"(?:channel/)([a-zA-Z0-9_-]{24})", youtube_url)
    if not match:
        await ctx.respond("❌ กรุณาใช้ URL แบบ `https://www.youtube.com/channel/UCxxxx` เท่านั้น")
        return

    channel_id = match.group(1)
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    guild_id = str(ctx.guild.id)
    announcement_configs[guild_id] = {
        "rss_url": rss_url,
        "discord_channel_id": ctx.channel.id,
        "last_video": None
    }

    save_config(announcement_configs)
    await ctx.respond(f"✅ ตั้งค่าเรียบร้อย! หากมีคลิปใหม่จากช่องนี้ บอทจะแจ้งเตือนที่นี่ 🎬")

# 🔄 เช็กทุก 5 นาที
@tasks.loop(minutes=5)
async def check_youtube():
    changed = False
    for guild_id, config in announcement_configs.items():
        feed = feedparser.parse(config["rss_url"])
        if not feed.entries:
            continue

        latest = feed.entries[0]
        video_title = latest.title
        video_url = latest.link

        if video_url != config.get("last_video"):
            announcement_configs[guild_id]["last_video"] = video_url
            changed = True

            channel = bot.get_channel(config["discord_channel_id"])
            if channel:
                await channel.send(f"🎬 มีคลิปใหม่บน YouTube: **{video_title}**\n{video_url}")

    if changed:
        save_config(announcement_configs)

# ✅ เริ่มต้นบอท
bot.run(TOKEN)
