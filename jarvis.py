import os
import random
import threading
import traceback
from flask import Flask
import httpx
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PORT = int(os.getenv("PORT", 5000))

if not TOKEN:
    print("❌ Missing DISCORD_BOT_TOKEN!")
    exit(1)

# Load fallback replies
def load_fallback_lines(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"⚠️ File {filename} not found.")
        return []

fallback_flirty = load_fallback_lines("fallback_flirty.txt")
fallback_funny = load_fallback_lines("fallback_funny.txt")
fallback_angry = load_fallback_lines("fallback_angry.txt")
fallback_roast = load_fallback_lines("fallback_roast.txt")
fallback_normal = load_fallback_lines("fallback_normal.txt")
all_fallback_replies = fallback_flirty + fallback_funny + fallback_angry + fallback_roast + fallback_normal

# Configure OpenAI (v1)
try:
    import openai
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
except ImportError:
    print("⚠️ openai module not installed. Fallback will be used.")

# Discord bot setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Flask server
app = Flask(__name__)

@app.route("/")
def home():
    return "🤖 JARVIS bot is alive and flirty!"

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

# Flirty GIFs
flirty_gifs = [
    "https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif",
    "https://media.giphy.com/media/l0IylOPCNkiqOgMyA/giphy.gif",
    "https://media.giphy.com/media/3o6Zt481isNVuQI1l6/giphy.gif"
]

# Gender detector
def detect_gender(username, roles):
    name = username.lower()
    role_names = [r.name.lower() for r in roles]
    if any(w in name for w in ["princess", "girl", "cutie"]) or "girl" in role_names:
        return "female"
    elif any(w in name for w in ["king", "raj", "boy"]) or "boy" in role_names:
        return "male"
    return "unknown"

# Smart AI response system
async def get_ai_reply(prompt):
    # Try OpenAI
    try:
        if OPENAI_API_KEY:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are JARVIS: a flirty, witty, human-like friend who chats like a real person."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message["content"].strip()
    except Exception as e:
        print("🔴 OpenAI Error:", e)

    # Try OpenRouter fallback
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        body = {
            "model": "openchat/openchat-7b",
            "messages": [
                {"role": "system", "content": "You are JARVIS: a flirty, witty, human-like friend who chats like a real person."},
                {"role": "user", "content": prompt}
            ]
        }
        async with httpx.AsyncClient() as client:
            res = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
            res.raise_for_status()
            data = res.json()
            return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print("🔴 OpenRouter failed too:", e)

    # Final fallback
    return random.choice(all_fallback_replies)

# Auto message every 1.5 hrs
@tasks.loop(seconds=5400)
async def auto_talk():
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                members = [m for m in guild.members if not m.bot]
                if members:
                    target = random.choice(members)
                    name = target.display_name
                    prompt = f"Start a flirty or friendly conversation with {name}."
                    msg = await get_ai_reply(prompt)
                    await channel.send(f"Hey {target.mention} 😏\n{msg}")
                break

enabled_channels = set()

@bot.event
async def on_ready():
    print(f"✅ JARVIS is online as {bot.user}")
    auto_talk.start()

@bot.event
async def on_message(message):
    if message.author == bot.user or message.guild is None:
        return

    content = message.content.lower()
    channel_id = message.channel.id
    mentioned = bot.user in message.mentions

    # Toggle ON/OFF
    if content == "!jarvis on":
        enabled_channels.add(channel_id)
        await message.channel.send("😇 JARVIS is now ON in this channel.")
        return

    if content == "!jarvis off":
        enabled_channels.discard(channel_id)
        await message.channel.send("😏 JARVIS is now OFF in this channel.")
        return

    if channel_id not in enabled_channels:
        return

    gender = detect_gender(message.author.name, message.author.roles)
    casual_keywords = ["hi", "hello", "bored", "single", "love", "miss me", "talk", "you there"]

    if mentioned or any(word in content for word in casual_keywords):
        if mentioned or random.random() < 0.3:
            prompt = f"{message.author.name} ({gender}) says: {message.content}. Reply casually or flirtatiously."
            reply = await get_ai_reply(prompt)
            await message.channel.send(reply)

            if random.randint(1, 4) == 1:
                await message.channel.send(random.choice(flirty_gifs))

    # Anyone can use this command to delete messages
    if content == "jarvis delete":
        deleted = await message.channel.purge(limit=100)
        await message.channel.send(f"Yes sir, {len(deleted)} messages deleted! 🧹")

    await bot.process_commands(message)

# Run Flask + Bot
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)
