import os

# Check the lock
lock = os.getenv("BOT_INSTANCE_LOCK", "0")
if lock == "1":
    print("Bot is already running. Exiting...")
    exit()  # Prevent starting a second instance

# Set the lock
os.environ["BOT_INSTANCE_LOCK"] = "1"


import discord
from zenora import APIClient
from flask import Flask, redirect, url_for, render_template, request, flash, session, jsonify

from .consts import premium_faqs, premium_types, langs, tz
from .config import URL_BASE, PY_ENV, BOT_TOKEN, CLIENT_ID, CLIENT_SECRET, OAUTH_URL, REDIRECT_URI, mongoURI_db, stripe_config

app = Flask(__name__)

app.config["SECRET_KEY"] = "mysecret"

bot = discord.Client(intents=discord.Intents.all())
client = APIClient(BOT_TOKEN, client_secret=CLIENT_SECRET)


def bearer_client():
  bearer_client = APIClient(session.get("token"), bearer=True)
  return bearer_client.users

## Main web ##
@app.route("/")
def index():
  if "token" not in session:
    return render_template("index.html", logInWithDiscord=OAUTH_URL)
  
  return render_template("index.html", user=None)


@bot.event
async def on_ready():
  print(f'We have logged in as {bot.user}')
  channel = bot.get_channel(1110277292124536953)
  await channel.send('Bot on vercel is online')

bot.run(BOT_TOKEN)