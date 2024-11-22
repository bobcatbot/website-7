from config import URL_BASE, PY_ENV, BOT_TOKEN, CLIENT_ID, CLIENT_SECRET, OAUTH_URL, REDIRECT_URI, mongoURI_db, stripe_config
from flask import Flask, redirect, url_for, render_template, request, flash, session, jsonify

app = Flask(__name__)

app.config["SECRET_KEY"] = "mysecret"

## Main web ##
@app.route("/")
def index():
  if "token" not in session:
    return render_template("index.html", logInWithDiscord=OAUTH_URL)
  
  return render_template("index.html", user=None)
