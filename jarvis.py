import os
import random
import threading
from flask import Flask

import discord
from discord.ext import commands, tasks
from openai import OpenAI

# --- Load environment variables ---
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PORT = int(os.getenv("PORT", 5000))

if not TOKEN or not OPENAI_API_KEY:
    print("❌ Missing DISCORD_BOT_TOKEN or OPENAI_API_KEY!")
    exit(1)

# --- Configure OpenAI with new client ---
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# --- Discord bot setup ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Flask server for uptime ---
app = Flask(__name__)

@app.route("/")
def home():
    return "🤖 JARVIS bot is alive and flirty!"

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

# --- Flirty GIFs ---
flirty_gifs = [
    "https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif",
    "https://media.giphy.com/media/l0IylOPCNkiqOgMyA/giphy.gif",
    "https://media.giphy.com/media/3o6Zt481isNVuQI1l6/giphy.gif"
]

# --- Gender detection helper ---
def detect_gender(username, roles):
    name = username.lower()
    role_names = [r.name.lower() for r in roles]
    if any(w in name for w in ["princess", "girl", "cutie"]) or "girl" in role_names:
        return "female"
    elif any(w in name for w in ["king", "raj", "boy"]) or "boy" in role_names:
        return "male"
    else:
        return "unknown"

# --- Get AI reply from OpenAI ---
async def get_ai_reply(prompt):
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a flirty, funny AI called JARVIS. Be sassy, humorous, casual and fun."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("🔴 OpenAI Error:", e)
        traceback.print_exc()
        return "Oops, even genius bots need a break 😅"

# --- Auto-talk loop ---
@tasks.loop(seconds=90)
async def auto_talk():
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                members = [m for m in guild.members if not m.bot]
                if members:
                    target = random.choice(members)
                    name = target.display_name
                    prompt = f"Start a casual, flirty or funny conversation with someone named {name}."
                    msg = await get_ai_reply(prompt)
                    await channel.send(f"Hey {target.mention} 😏\n{msg}")
                break

# --- Discord Events ---
@bot.event
async def on_ready():
    print(f"✅ JARVIS is online as {bot.user}")
    auto_talk.start()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower()
    gender = detect_gender(message.author.name, message.author.roles)

    if any(word in content for word in ["hi", "hello", "bored", "single", "love", "miss me"]):
        prompt = f"{message.author.name} ({gender}) says: {message.content}. Reply flirtatiously or humorously."
        reply = await get_ai_reply(prompt)
        await message.channel.send(reply)

        if random.randint(1, 4) == 1:
            await message.channel.send(random.choice(flirty_gifs))

    if content == "jarvis delete":
        if message.channel.permissions_for(message.author).manage_messages:
            deleted = await message.channel.purge(limit=100)
            await message.channel.send(f"Yes sir, {len(deleted)} messages deleted! 🧹")
        else:
            await message.channel.send("You need permissions for that, cutie 💅")

    await bot.process_commands(message)

# --- Start Flask and Bot ---
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)
