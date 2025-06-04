# JARVIS 3.0: Full Auto-Flirty, Intelligent Discord Bot

import discord
from discord.ext import commands, tasks
import openai
import random
import aiohttp
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

flirty_gifs = [
    "https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif",
    "https://media.giphy.com/media/l0IylOPCNkiqOgMyA/giphy.gif",
    "https://media.giphy.com/media/3o6Zt481isNVuQI1l6/giphy.gif"
]

# --- Gender Detection ---
def detect_gender(username, roles):
    name = username.lower()
    role_names = [r.name.lower() for r in roles]
    if any(word in name for word in ["princess", "girl", "cutie"]) or "girl" in role_names:
        return "female"
    elif any(word in name for word in ["king", "raj", "boy"]) or "boy" in role_names:
        return "male"
    else:
        return "unknown"

# --- Generate OpenAI Chat Reply ---
async def get_ai_reply(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a flirty, funny AI called JARVIS. Talk casually, add emojis, pickup lines, and sass."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "Oops, even genius bots need a break 😅"

# --- Auto Talker ---
@tasks.loop(seconds=90)
async def auto_talk():
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                members = [m for m in guild.members if not m.bot]
                if members:
                    target = random.choice(members)
                    name = target.display_name
                    prompt = f"Start a casual, flirty or funny convo with someone named {name}"
                    msg = await get_ai_reply(prompt)
                    await channel.send(f"Hey {target.mention} 👀\n{msg}")
                break

# --- On Ready ---
@bot.event
async def on_ready():
    print(f"JARVIS is online as {bot.user}")
    auto_talk.start()

# --- Smart Listener ---
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower()
    gender = detect_gender(message.author.name, message.author.roles)
    if any(w in content for w in ["hi", "hello", "bored", "single", "love", "miss me"]):
        prompt = f"{message.author.name} ({gender}) says: {message.content}. Reply flirtatiously or humorously."
        reply = await get_ai_reply(prompt)
        await message.channel.send(reply)

        # 25% chance to add a flirty GIF
        if random.randint(1, 4) == 1:
            await message.channel.send(random.choice(flirty_gifs))

    if content == "jarvis delete":
        if message.channel.permissions_for(message.author).manage_messages:
            deleted = await message.channel.purge(limit=100)
            await message.channel.send(f"Yes sir, {len(deleted)} messages deleted! 🧹")
        else:
            await message.channel.send("You need permissions for that, cutie 💅")

    await bot.process_commands(message)

bot.run(TOKEN)
