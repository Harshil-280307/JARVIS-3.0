# jarvis.py

import os
import random
import threading
import traceback
from flask import Flask
import httpx
import discord
from discord.ext import commands, tasks
from openai import OpenAI

# --- Load environment variables ---
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PORT = int(os.getenv("PORT", 5000))

if not TOKEN:
    print("❌ Missing DISCORD_BOT_TOKEN!")
    exit(1)

# --- Load fallback replies ---
def load_fallback_lines(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

fallback_flirty = load_fallback_lines("fallback_flirty.txt")
fallback_funny = load_fallback_lines("fallback_funny.txt")
fallback_angry = load_fallback_lines("fallback_angry.txt")
fallback_roast = load_fallback_lines("fallback_roast.txt")
fallback_normal = load_fallback_lines("fallback_normal.txt")
all_fallback_replies = fallback_flirty + fallback_funny + fallback_angry + fallback_roast + fallback_normal

# --- AI Client Setup ---
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# --- Discord bot ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Flask app ---
app = Flask(__name__)
@app.route("/")
def home():
    return "🤖 JARVIS bot is alive and flirty!"

def run_flask():
