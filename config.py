import os
from dotenv import load_dotenv

load_dotenv()

URL_BASE = os.getenv('URL_BASE')
PY_ENV = os.getenv('ENV')

BOT_TOKEN = os.getenv('BOT_TOKEN')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

WEBHOOK_PREM = os.getenv('DISCORD_WEBHOOK_PREM')

REDIRECT_URI = f"{URL_BASE}/oauth/callback"
OAUTH_URL = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify%20guilds%20email%20guilds.join"

mongoURI_db = os.getenv('mongoURI_db')
mongoURI_dash = os.getenv('mongoURI_dash')
mongo_cdn = os.getenv('mongoURI_cdn')

stripe_config = {
  "PUBLIC_KEY": os.getenv('STRIPE_PUBLIC_KEY'),
  "SECRET_KEY": os.getenv('STRIPE_SECRET_KEY'),
  "WH_KEY": os.getenv('STRIPE_WH_KEY')
}