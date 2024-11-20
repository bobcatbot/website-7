import logging, asyncio
import discord, pymongo, pytz, requests, stripe
from plugins import fetch_plugins
from consts import premium_faqs, premium_types, langs, tz
from config import URL_BASE, PY_ENV, BOT_TOKEN, CLIENT_ID, CLIENT_SECRET, OAUTH_URL, REDIRECT_URI, mongoURI_db, stripe_config
from threading import Thread
from zenora import APIClient
from flask import Flask, redirect, url_for, render_template, request, flash, session, jsonify
from datetime import datetime
from dateutil.relativedelta import relativedelta

app = Flask(__name__)

app.config["SECRET_KEY"] = "mysecret"
app.config["STRIPE_PUBLIC_KEY"] = stripe_config["PUBLIC_KEY"]
app.config["STRIPE_SECRET_KEY"] = stripe_config["SECRET_KEY"]
app.config["STRIPE_WEBHOOK_KEY"] = stripe_config["WH_KEY"]

bot = discord.Client(intents=discord.Intents.all())
client = APIClient(BOT_TOKEN, client_secret=CLIENT_SECRET)

stripe.api_key = app.config["STRIPE_SECRET_KEY"]

# logging.getLogger('werkzeug').setLevel(logging.ERROR)

MongoClientBot = pymongo.MongoClient(mongoURI_db)
db = MongoClientBot['Bot']['Bot']

def bearer_client():
  bearer_client = APIClient(session.get("token"), bearer=True)
  return bearer_client.users

def get_server_config(guild: int, all=False):
  try:
    guildID = guild.id
  except AttributeError:
    guildID = guild

  data: dict = db.find_one({"_id": str(guildID)})
  if data is None:
    return None

  if all:
    return data
  return data["Bot"]

def get_dash_config(guild: int):
  try:
    id = str(guild.id)
  except AttributeError:
    id = str(guild)

  data = db.find_one({'_id': id})
  if data is None:
    return None

  return data["Dash"]

def update_config(guild_id: int, key: str, value):
  try:
    id = str(guild_id.id)
  except AttributeError:
    id = str(guild_id)

  d = db.update_one(
    { '_id': id },
    { '$set': { key: value } }
  )
  if d:
    return True
  return False

# TODO: 403, 410, 500
@app.errorhandler(404)
async def redirect_error_page(e):
  return render_template('error/404.html'), 404

## Main web ##
@app.route("/")
async def index():
  if not "token" in session:
    return render_template("index.html", logInWithDiscord=OAUTH_URL)

  current_user = bearer_client().get_current_user()
  return render_template("index.html", user=current_user)

@app.route("/plugins/management")
async def web_token_management():
  if not "token" in session:
    return render_template("web-plugins/management.html", logInWithDiscord=OAUTH_URL)

  current_user = bearer_client().get_current_user()
  return render_template("web-plugins/management.html", user=current_user)

@app.route("/plugins/utilities")
async def web_token_utilities():
  if not "token" in session:
    return render_template("web-plugins/utilities.html", logInWithDiscord=OAUTH_URL)

  current_user = bearer_client().get_current_user()
  return render_template("web-plugins/utilities.html", user=current_user)

@app.route("/plugins/engagement-and-fun")
async def web_token_engagement():
  if not "token" in session:
    return render_template("web-plugins/engagement-and-fun.html", logInWithDiscord=OAUTH_URL)

  current_user = bearer_client().get_current_user()
  return render_template("web-plugins/engagement-and-fun.html", user=current_user)

@app.route('/contact-us') # update
async def contactUs():
  if not "token" in session:
    return render_template("contact-us.html", logInWithDiscord=OAUTH_URL)

  current_user = bearer_client().get_current_user()
  return render_template("contact-us.html", user=current_user)

@app.route('/thanks')
async def thanks():
  if not "token" in session:
    return render_template("thanks.html", logInWithDiscord=OAUTH_URL)

  current_user = bearer_client().get_current_user()
  return render_template("thanks.html", user=current_user)

@app.route('/terms')
async def terms():
  if not "token" in session:
    return render_template('terms.html', logInWithDiscord=OAUTH_URL)

  current_user = bearer_client().get_current_user()
  return render_template('terms.html', user=current_user)

"""@app.route("/privacy")
async def privacy():
  if not "token" in session:
    return render_template('privacy.html', logInWithDiscord=OAUTH_URL)

  current_user = bearer_client().get_current_user()
  return render_template('privacy.html', user=current_user)"""

## Dashboard ##
@app.context_processor
def utility_processor():
  def plugs(guild):
    """Retrieve plugins based on guild"""
    dash_data = get_dash_config(guild)
    plugins_list = fetch_plugins(dash_data)
    return plugins_list

  def get_plugin(guild, plugin):
    plug_list = plugs(guild)
    for _item, _plugin in plug_list:
      if _item != plugin:
        continue
      return _plugin

  def GetUserGuilds():
    g = []
    user_guilds = bearer_client().get_my_guilds()
    guild_ids = [gID.id for gID in bot.guilds]
    for _guild in user_guilds:
      if _guild.id in guild_ids:
        _guild.active = True
        g.append(_guild)
    return g

  def server_config(guild):
    return get_server_config(guild, True)

  return {'plugins': plugs, 'get_plugin': get_plugin, 'guilds': GetUserGuilds,  'guild_models': guild_models, 'server_config': server_config}

## Auth ##
@app.route("/oauth/login")
async def login():  
  return redirect(OAUTH_URL)

@app.route("/oauth/logout")
async def logout():
  session.pop("token")
  flash("Logged you out...", "log-out")
  return redirect(url_for("index"))

@app.route("/oauth/callback")
async def oauth_callback():
  try:
    code = request.args.get("code")
    token = client.oauth.get_access_token(code, REDIRECT_URI).access_token
    session["token"] = token
    session["lastSignedIn"] = datetime.now()

    user = bearer_client().get_current_user()
    flash(f'Logged in as {user.username}#{user.discriminator} !', 'log-in')

    redirect_url = session.get('redirect', url_for("index"))
    session.pop('redirect')
    return redirect(redirect_url)
  except:
    flash('Oh no, something went wrong during authentication', 'login-error')
    return redirect(url_for("index"))

def login_required(f):
  from functools import wraps

  @wraps(f)
  async def decorated_function(*args, **kwargs):
    if 'token' not in session:
      session['redirect'] = request.url
      return render_template("login.html", logInWithDiscord=url_for('login'))
    return await f(*args, **kwargs)
  return decorated_function

## Leaderboard ##
@app.route("/leaderboard/<data>", methods=['GET', 'POST'])
@login_required
async def leaderboard_home(data):
  current_user = bearer_client().get_current_user()

  if request.method == 'POST':
    json = request.get_json()
    guild = bot.get_guild(int(json['guild_id']))

    leveling = get_server_config(guild).get('leveling')

    if 'reset' in json['key']:
      if 'user_id' in json:
        u = json['user_id']
        update_config(guild, key=f'Bot.leveling.{u}.exp', value=0)
        update_config(guild, key=f'Bot.leveling.{u}.lvl', value=0)
        return jsonify({'status': 200})

      for user in leveling:
        lvl_user = leveling[user]
        lvl_user['exp'] = 0
        lvl_user['lvl'] = 0
        update_config(guild, key=f'Bot.leveling.{user}', value=lvl_user)
      return jsonify({'status': 200})

    if json['key'] == 'BannerRemove':
      #update_config(guild, key='Dash.leveling.leaderboard.banner', value="")
      return jsonify({'status': 200})
    return jsonify({'status': 400})

  for db_data in db.find():
    if db_data['Dash']['leveling']['leaderboard']['url'] == "":
      url = db_data['Dash']['leveling']['leaderboard']['url']
    else:
      url = db_data["_id"] # guild id

    if url == data:
      db_data = db_data
    break

  guild = bot.get_guild(int(db_data['_id']))

  lvl_config = get_dash_config(guild).get('leveling')

  if not lvl_config['leaderboard']['public'] and current_user.id not in [member.id for member in guild.members]:
    flash('You are not allowed to view the leaderboard', 'error')
    return redirect(url_for('index'))

  users = []
  lvl_users = get_server_config(guild).get('leveling')

  sorted_players = sorted(lvl_users.items(), key=lambda x: int(x[1]['lvl']), reverse=True)

  for idx, (player_id, data) in enumerate(sorted_players, start=1):    
    player = bot.get_user(int(player_id))
    data['msg_count'] = lvl_users[player_id]['msg_count'] if 'msg_count' in lvl_users[player_id] else 0
    users.append((idx, (player, data)))

  user = guild.get_member(current_user.id)
  gp = user.guild_permissions

  return render_template("dashboard/leaderboard.html", user=current_user, guild_permissions=gp, guild=guild, data=lvl_config, users=users)

## Forms ##
@app.route("/form/<int:guild_id>/<form_id>", methods=['GET', 'POST'])
@login_required
async def form(guild_id, form_id):
  current_user = bearer_client().get_current_user()
  guild = bot.get_guild(guild_id)
  server_config = get_server_config(guild, True).get('settings')

  if request.method == 'POST':
    data = request.get_json()

    forms = get_server_config(guild).get('forms')
    for _form in forms:
      if _form['id'] != form_id:
        continue
      form = _form

    form_idx = forms.index(form)

    form['responses'].append(data)
    update_config(guild, f'Bot.forms.{form_idx}.responses', form['responses'])

    channel = guild.get_channel(int(form['settings']['submission_channel']))
    async def send_message():
      submitted_at = datetime.fromisoformat(data['submitted_at'])
      embed = discord.Embed(
        title=f"{form['name']} (#{len(form['responses'])})", 
        color=0x5865F2, timestamp=submitted_at, 
      ) 

      for index, question in enumerate(form['questions']):
        embed.add_field(name=question['title'], value=data['answers'][index], inline=False)        

      embed.set_footer(text=f"User ID: {data['user']['id']}")
      msg = await channel.send(embed=embed)

      form_reactions = form['settings']['reactions']
      if form_reactions['status'] == True and form_reactions['emojis']:
        for emoji in form_reactions['emojis']:
          await msg.add_reaction(emoji)

    bot.loop.create_task(send_message())
    return jsonify({'status': 200})

  forms = get_server_config(guild).get('forms')

  for form in forms:
    if form['id'] != form_id:
      continue
    data = form

  return render_template("form.html", user=current_user, guild=guild, data=data)
@app.route("/form/<int:guild_id>/<form_id>/submissions")
@login_required
async def form_submissions(guild_id, form_id):
  current_user = bearer_client().get_current_user()
  guild = bot.get_guild(guild_id)

  user = guild.get_member(current_user.id)

  forms = get_server_config(guild).get('forms')

  for _form in forms:
    if _form['id'] != form_id:
      continue
    form = _form

  if (  # Owner, Admin
    user.guild_permissions.administrator == False or
    user.guild.owner == False
  ):
    return redirect(url_for('index'))

  if form['settings']['submission_viewers'] or form['settings']['submission_managers'] and not any(
    role in form['settings']['submission_viewers'] or
    role in form ['settings']['submission_managers']
    for role in user.roles
  ):
    return redirect(url_for('index'))

  response_id = request.args.get('response_id')
  if response_id:
    for response in form['responses']:
      if response['id'] != response_id:
        continue
      data = response
  else:
    data = None

  return render_template("form_subs.html", user=current_user, guild=guild, form=form, data=data)


@app.route("/dashboard")
@login_required
async def guilds():
  guilds = []
  current_user = bearer_client().get_current_user()
  user_guilds = bearer_client().get_my_guilds()
  guild_ids = [gID.id for gID in bot.guilds]

  for guild in user_guilds:
    if (  # Owner, Admin
      int(guild.permissions) & 0x8 == 0x8 or 
      guild.is_owner == True
    ):
      guild.perm = "Owner" if guild.owner == True else "Admin"
      guild.btn_name = "Go" if guild.id in guild_ids else "Setup"
      guild.color = "#5865F2" if guild.id in guild_ids else "#36393f"

      guilds.append(guild)

  guilds.sort(key=lambda x: x.btn_name == "Go", reverse=True)
  guilds.sort(key=lambda x: x.color == "#5865f2", reverse=True)
  return render_template("dashboard/guilds.html", user=current_user, guilds=guilds)

@app.route("/dashboard/<int:guild_id>")
@login_required
async def dashboard_home(guild_id):
  current_user = bearer_client().get_current_user()
  guild = bot.get_guild(guild_id)

  session['guild_id'] = guild.id

  if guild is None:
    return redirect(f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&scope=bot&permissions=8&guild_id={guild_id}&response_type=code&redirect_uri={URL_BASE}/dashboard")

  return render_template("dashboard/dashboard.html", user=current_user, guild=guild)

@app.route("/dashboard/<int:guild_id>/settings")
@login_required
async def settings(guild_id):
  current_user = bearer_client().get_current_user()
  guild = bot.get_guild(guild_id)

  data = get_server_config(guild, True).get('settings')
  return render_template("dashboard/settings.html", user=current_user, guild=guild, data=data, languages=langs, timezones=tz)

@app.route("/dashboard/<int:guild_id>/premium", methods=["GET", "POST"])
@login_required
async def premium(guild_id):
  import aiohttp
  current_user = bearer_client().get_current_user()
  guild = bot.get_guild(guild_id)

  prem_data = get_server_config(guild, True).get('premium')

  if prem_data['status'] == False:

    if request.method == 'POST':
      data = request.get_json()
      config = get_server_config(guild, True)['settings']

      if not prem_data['code']:
        return

      wh_url = 'https://discord.com/api/webhooks/1175420459513282582/_wCZUkeNlIG3P3Fy1bfLJQVY_liEN5L9NR10rcLukwJlSSUU0GQuzQXAFt_W5qaDib7o'
      async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(wh_url, session=session)

        code = data['code']

        if prem_data['code'] == code:
          user = bot.get_user(int(data['user_id']))

          date = datetime.now(pytz.timezone(config['timezone']))
          prem_data = {
            'id': code, 'status': True, 'active': True, 'plan': 'lifetime', 'customer': '', 'user_id': user.id, 'subscribed_at': date,
            'code_expired': True
          }
          update_config(guild, 'premium', prem_data)

          embed = discord.Embed(title='Premium Activated', description=f'**{code}** has been used to activated premium.', color=0x5865F2)
          embed.set_thumbnail(url=guild.icon.url)
          embed.add_field(name='Guild', value=f'{guild.name} ({guild.id})', inline=False)
          embed.add_field(name='Activated By', value=f'{user.mention} (@{user.name} - {user.id})', inline=False)
          await webhook.send(embed=embed)
      return jsonify({ 'status': 'success' })

    return render_template("dashboard/premium/index.html", user=current_user, guild=guild, data=prem_data, faqs=premium_faqs, types=premium_types)

  createdAt_later = "Never"
  days_countdown = "0"
  if prem_data['plan'] == 'monthly':
    date = prem_data['subscribed_at'] #+ relativedelta(months=1)
    days_countdown = (date - datetime.now()).days
    createdAt_later = date.strftime("%B %d %Y")
  if prem_data['plan'] == 'yearly':
    date = prem_data['subscribed_at'] #+ relativedelta(years=1)
    days_countdown = (date - datetime.now()).days
    createdAt_later = date.strftime("%B %d %Y")

  user = bot.get_user(int(prem_data['user_id']))

  data = {
    'next_bill': createdAt_later,
    'countdown': days_countdown,
    'user': {
      'avatar': user.avatar.url,
      'name': user.name,
    },
  } | prem_data

  return render_template("dashboard/premium/manage.html", user=current_user, guild=guild, data=data, types=premium_types)

@app.route("/dashboard/<int:guild_id>/notifications", methods=["GET", "POST"])
@login_required
async def notifications(guild_id):
  current_user = bearer_client().get_current_user()
  guild = bot.get_guild(guild_id)

  data = get_server_config(guild, True).get('notifications')

  if request.method == 'POST':
    res = request.get_json()
    for _notification in data:
      if _notification['id'] == res['id']:
        notif = _notification

    notif_idx = data.index(notif)
    res.pop('id')
    for key, val in res.items():
      update_config(guild.id, f'notifications.{notif_idx}.{key}', val)
    return jsonify({'status': 'success', 'message': 'Successfully updated notifications'})

  notifications_by_date = {}

  for notification in data:
    date = notification['created_at']['date']
    if not date in notifications_by_date:
      notifications_by_date[date] = []
    notifications_by_date[date].append(notification)
    notifications_by_date[date].sort(key=lambda x: x['created_at']['time'], reverse=True)

  notifications_by_date = dict(reversed(list(notifications_by_date.items())))

  return render_template("dashboard/notifications.html", user=current_user, guild=guild, data=data, notifications=notifications_by_date)

@app.route("/dashboard/<int:guild_id>/welcome")
@login_required
async def welcome(guild_id):
  current_user = bearer_client().get_current_user()
  guild = bot.get_guild(guild_id)

  data = get_dash_config(guild).get('welcome')
  return render_template("dashboard/plugins/welcome.html", user=current_user, guild=guild, data=data)

@app.route("/dashboard/<int:guild_id>/moderator")
@login_required
async def moderation(guild_id):
  current_user = bearer_client().get_current_user()
  guild = bot.get_guild(guild_id)

  dash_data = get_dash_config(guild).get('moderation')
  logs = dash_data['logging']
  return render_template("dashboard/plugins/moderation.html", user=current_user, guild=guild, data=dash_data, logging=logs)

@app.route("/dashboard/<int:guild_id>/verification", methods=['GET', 'POST', 'UPDATE'])
@login_required
async def verify(guild_id):
  current_user = bearer_client().get_current_user()
  guild = bot.get_guild(guild_id)

  if request.method == 'POST':
    data = request.get_json()
    # print(data)
    config = get_dash_config(guild)['verification']

    async def send_message():
      embed = discord.Embed.from_dict(data['embed'])
      print(embed.to_dict())

      style = {
        'secondary': discord.ButtonStyle.gray,
        'blurple': discord.ButtonStyle.blurple,
        'danger': discord.ButtonStyle.red,
        'success': discord.ButtonStyle.green,
      }[data['btn']['color']]

      view = discord.ui.View()
      view.add_item(discord.ui.Button(
        emoji=data['btn']['emoji'] if data['btn']['emoji'] else None, 
        label=data['btn']['title'], 
        style=style,
        custom_id='Verification'
      ))

      if config.get('message_published', False):
        channel = guild.get_channel(int(config['channel']))
        msg = await channel.fetch_message(int(config['message_id']))
        await msg.edit(embed=embed, view=view)
        return

      role = guild.get_role(int(config['role']))
      if not role:
        role = await guild.create_role(name='Verified', reason='Enabled verification system')

        update_config(guild, 'Dash.verification.role', role.id)

      channel = guild.get_channel(int(config['channel']))
      if not channel:
        channel = await guild.create_text_channel('verification', reason='Enabled verification system', overwrites={
          guild.default_role: discord.PermissionOverwrite(
            read_messages=True,
            send_messages=False,
            read_message_history=True,
          ),
          role: discord.PermissionOverwrite(
            read_messages=True,
            send_messages=False,
            read_message_history=True,
          )
        })

        update_config(guild, 'Dash.verification.channel', channel.id)

      await channel.set_permissions(
        guild.default_role,
        overwrite=discord.PermissionOverwrite(
          read_messages=True,
          send_messages=False,
        )
      )
      await channel.set_permissions(
        role,
        overwrite=discord.PermissionOverwrite(
          read_messages=False,
          send_messages=False,
        )
      )

      await guild.default_role.edit( # @everyone
        reason="Verification system enabled",
        permissions=discord.Permissions(
          read_messages=False,
        )
      )

      if role.id == int(config['role']):
        await role.edit(
          reason="Verification system enabled",
          permissions=discord.Permissions(
            read_messages=True
          )
        )

      msg = await channel.send(embed=embed, view=view)
      update_config(guild, 'Dash.verification.message_id', f'{msg.id}')
      update_config(guild, 'Dash.verification.message_published', True)
    bot.loop.create_task(send_message())

    return jsonify({'status': 'success', 'message': 'Successfully published verification message'})

  if request.method == 'UPDATE':
    data = request.get_json()
    print(data)

    config = get_dash_config(guild)['verification']

    return jsonify({'status': 'success', 'message': 'Successfully updated verification message'})

  data = get_dash_config(guild).get('verification')
  return render_template("dashboard/plugins/verification.html", user=current_user, guild=guild, data=data)

# @app.route("/dashboard/<int:guild_id>/embeds")
@login_required
async def embed_messages(guild_id):
  current_user = bearer_client().get_current_user()
  guild = bot.get_guild(guild_id)

  data = get_dash_config(guild).get('embeds')
  return render_template("dashboard/plugins/embeds/em_index.html", user=current_user, guild=guild, data=data)
# @app.route("/dashboard/<int:guild_id>/embeds/creation", methods=['GET', 'POST'])
@login_required
async def embed_messages_create(guild_id):
  current_user = bearer_client().get_current_user()
  guild = bot.get_guild(guild_id)

  if request.method == 'POST':
    data = request.form
    print(data)
    return

  data = get_dash_config(guild).get('embeds')
  return render_template("dashboard/plugins/embeds/em_create.html", user=current_user, guild=guild, data=data)

@app.route("/dashboard/<int:guild_id>/starboard")
@login_required
async def starboard(guild_id):
  current_user = bearer_client().get_current_user()
  guild = bot.get_guild(guild_id)

  dash_data = get_dash_config(guild.id).get('starboard')
  return render_template("dashboard/plugins/starboard.html", user=current_user, guild=guild, data=dash_data)

## Forms ##
@app.route("/dashboard/<int:guild_id>/forms")
@login_required
async def forms(guild_id):
  current_user = bearer_client().get_current_user()
  guild = bot.get_guild(guild_id)

  data = get_server_config(guild).get('forms')
  plugin = get_dash_config(guild).get('forms')
  return render_template("dashboard/plugins/forms/form_index.html", user=current_user, guild=guild, data=data, plugin=plugin)
@app.route("/dashboard/<int:guild_id>/forms/creation", methods=['GET', 'POST'])
@login_required
async def forms_create(guild_id):
  current_user = bearer_client().get_current_user()
  guild = bot.get_guild(guild_id)

  if request.method == 'POST':
    data = request.get_json()

    def generateId(length=8):
      import random, string
      letters = string.ascii_letters + string.digits
      return ''.join(random.choice(letters) for i in range(length))

    data['id'] = generateId(12)

    forms = get_server_config(guild).get('forms')

    for key, val in data.items():
      update_config(guild.id, f'Bot.forms.{len(forms)}.{key}', val)

    flash(f"Successfully created form {data['id']}", 'success')
    return jsonify({'status': 'success', 'message': f"Successfully created form {data['id']}"})

  return render_template("dashboard/plugins/forms/form_create.html", user=current_user, guild=guild)
@app.route("/dashboard/<int:guild_id>/forms/<form_id>/edit", methods=['GET', 'POST', 'DELETE'])
@login_required
async def forms_edit(guild_id, form_id):
  current_user = bearer_client().get_current_user()
  guild = bot.get_guild(guild_id)

  if request.method == 'POST':
    data = request.get_json()

    forms = get_server_config(guild).get('forms')
    for _form in forms:
      if _form['id'] != form_id:
        continue
      form = _form

    form_idx = forms.index(form)

    for key, val in data.items():
      update_config(guild.id, f'Bot.forms.{form_idx}.{key}', val)

    return jsonify({'status': 'success', 'message': 'Successfully updated form'})

  if request.method == 'DELETE':
    forms = get_server_config(guild).get('forms')
    for _form in forms:
      if _form['id'] != form_id:
        continue
      form = _form

    form_idx = forms.index(form)
    forms.pop(form_idx)
    update_config(guild.id, 'Bot.forms', forms)
    return jsonify({'status': 'success', 'message': 'Successfully deleted form'})

  forms = get_server_config(guild).get('forms')

  for form in forms:
    if form['id'] != form_id:
      continue
    data = form

  return render_template("dashboard/plugins/forms/form_edit.html", user=current_user, guild=guild, data=data)

@app.route("/dashboard/<int:guild_id>/leveling")
@login_required
async def levelling(guild_id):
  current_user = bearer_client().get_current_user()
  guild = bot.get_guild(guild_id)

  dash_data = get_dash_config(guild.id).get('leveling')

  rank_cards = requests.post('https://cdn.bobcatbot.xyz/bot-level-cards')
  cards = rank_cards.json()
  server_card_url = f'https://cdn.bobcatbot.xyz/static/lvl-cards'
  return render_template("dashboard/plugins/leveling.html", user=current_user, guild=guild, data=dash_data, server_cards=cards, server_card_url=server_card_url)

@app.route("/dashboard/<int:guild_id>/economy")
@login_required
async def economy(guild_id):
  current_user = bearer_client().get_current_user()
  guild = bot.get_guild(guild_id)

  dash = get_dash_config(guild.id).get('economy')
  dash_data = dash | {'num_items': len(dash['shop'])}
  return render_template("dashboard/plugins/economy.html", user=current_user, guild=guild, data=dash_data)


@app.route("/dashboard/<int:guild_id>/test")
@login_required
async def test_route(guild_id):
  current_user = bearer_client().get_current_user()
  guild = bot.get_guild(guild_id)

  channel = guild.get_channel(1031184603756646400)
  async def send_message():
    embed = discord.Embed(
      title=f"Verification Test",
      description="Please click the button below to verify yourself (from dashboard)",
      color=0x5865F2,
    )

    view = discord.ui.View()
    view.add_item(discord.ui.Button(label='Verify', style=discord.ButtonStyle.green, custom_id='Verification'))

    await channel.send(embed=embed, view=view)
  bot.loop.create_task(send_message())

  return 'is this working?'


## other ##
@app.route("/dashboard/<int:guild_id>/data/post", methods=["POST"])
async def data_post(guild_id):
  data = request.get_json().items()
  guild = bot.get_guild(guild_id)

  for key, val in data:
    if key == "EconomyUsers":
      server = get_server_config(guild)['economy']
      for user in server:
        server[user]['wallet'] = 0
        server[user]['bank'] = 0
        server[user]['bag'] = []
        update_config(guild, 'Bot.economy', server)
      break

    settings_configs = ['settings.language', 'settings.timezone', 'settings.color']
    if key in settings_configs:
      update_config(guild, key, val)
      break

    update_config(guild, "Dash." + key, val)
  return {'status': 'success', 'message': 'Successfully updated data'}

@app.route("/get_user_guilds", methods=["POST"])
async def get_guilds():
  import json

  guilds = []
  user_guilds = bearer_client().get_my_guilds()
  guild_ids = [gID.id for gID in bot.guilds]

  for _guild in user_guilds:
    guilds.append({
      'id': _guild.id,
      'name': _guild.name,
      'icon': _guild.icon_url if _guild.icon_url else '/static/discord-logo.png',
      'unavailable': True, #  _guild.unavailable,
      'permissions': _guild.permissions,
      'active': True if _guild.id in guild_ids else False,
    })

  Guilds = json.dumps(guilds)
  return jsonify({'guilds': Guilds})

## Stripe ##
@app.route('/<int:guild_id>/stripe/pay/<type>')
def stripe_pay(guild_id, type):
  current_user = bearer_client().get_current_user()
  guild = bot.get_guild(guild_id)

  session = stripe.checkout.Session.create(
    payment_method_types=['card'],
    line_items=[{
      'price': premium_types[type]['price_id'],
      'quantity': 1,
    }],
    mode=premium_types[type]['mode'],
    customer_email=current_user.email,
    success_url=url_for('premium', _external=True, guild_id=guild.id) + '?session_id={CHECKOUT_SESSION_ID}',
    cancel_url =url_for('premium', _external=True, guild_id=guild.id),
    metadata={
      "guild_id": guild.id,
      "user_id": current_user.id
    }
  )
  return {
    'checkout_session_id': session['id'], 
    'checkout_public_key': app.config['STRIPE_PUBLIC_KEY']
  }
@app.route('/stripe/portal/<customer_id>', methods=['POST'])
def stripe_portal(customer_id):
  for data in db.find():
    guild_id = data['_id']
    premium = data['premium']

    if premium['customer'] != customer_id:
      continue

    portal = stripe.billing_portal.Session.create(
      customer=premium['customer'],
      return_url=url_for('premium', _external=True, guild_id=guild_id),
    )
    return {
      'url': portal["url"],
      'checkout_public_key': app.config['STRIPE_PUBLIC_KEY']
    }
  return { 'error': 'customer id not found' }, 400

@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
  if request.content_length > 1024 * 1024:
    print('REQUEST TOO BIG')
    return "REQUEST TOO BIG", 400

  payload = request.get_data();
  sig_header = request.environ.get('HTTP_STRIPE_SIGNATURE')
  endpoint_secret = app.config["STRIPE_WEBHOOK_KEY"]
  event = None

  try:
    event = stripe.Webhook.construct_event(
      payload, sig_header, endpoint_secret
    )
  except ValueError:
    # Invalid payload
    print('INVALID PAYLOAD')
    return {}, 400
  except stripe.error.SignatureVerificationError:
    # Invalid signature
    print('INVALID SIGNATURE')
    return {}, 400

  # Handle the checkout.session.completed event
  if event['type'] == 'checkout.session.completed':
    session = event['data']['object']

    if not session:
      return {}, 400

    line_items = stripe.checkout.Session.list_line_items(session['id'], limit=1)

    if session["mode"] == "subscription":
      print('subscription mode')
      subscription = stripe.Subscription.retrieve(session["subscription"])
      # print(subscription)

      guild_id = session['metadata']['guild_id']
      user_id = session['metadata']['user_id']

      server_config = get_server_config(guild_id, True)['settings']

      datetime_utc = datetime.utcfromtimestamp(session["created"])
      createdAt = datetime_utc.astimezone(pytz.timezone(server_config['timezone']))

      billing_history = []
      billing_history.append({
        "invoice": session['invoice'],
        "created": datetime.now(pytz.timezone(server_config['timezone'])),
      })

      data = {
        "id": session['subscription'],
        "status": True,
        "active": session['status'] == 'complete',
        "plan": line_items['data'][0]['description'].lower(),
        "customer": session['customer'],
        "user_id": user_id,
        "subscribed_at": createdAt,
      }
      update_config(int(guild_id), 'premium', data)

    if session["mode"] == "payment":
      print('payment mode')
      guild_id = session['metadata']['guild_id']
      user_id = session['metadata']['user_id']

      server_config = get_server_config(guild_id, True)['settings']

      datetime_utc = datetime.utcfromtimestamp(session["created"])
      createdAt = datetime_utc.astimezone(pytz.timezone(server_config['timezone']))

      billing_history = []
      billing_history.append({
        "invoice": session['invoice'],
        "created": datetime.now(pytz.timezone(server_config['timezone'])),
      })

      sub = session['subscription']
      plan = line_items['data'][0]['description'].lower()
      data = {
        "id": sub, "status": True, "active": True, "plan": plan, "customer": session['customer'], "user_id": user_id, "subscribed_at": createdAt,
      }
      update_config(int(guild_id), 'premium', data)
    return {}

  # Handle the customer.subscription.updated event
  if event['type'] == 'customer.subscription.updated':
    print('customer subscription updated event received')
    subscription = event['data']['object']

    if not subscription:
      return {}, 400

    for data in db.find():
      guild_id = data['_id']
      premium = data['premium']
      config = data['settings']

    if premium['status'] == False:
      return { 'error': 'premium status is false' }, 400

    if premium['id'] == subscription['id']:

      if subscription['cancel_at'] != None or subscription['canceled_at'] != None: # subscription is cancelled
        update_config(int(guild_id), 'premium.status', False)
        update_config(int(guild_id), 'premium.active', False)
        update_config(int(guild_id), 'premium.canceled_at', datetime.now(pytz.timezone(config['timezone'])))
        return { 'status': 'success', 'msg': 'user canceled subscription' }, 200
      #
      datetime_utc = datetime.utcfromtimestamp(subscription["current_period_end"])
      updatedAt = datetime_utc.astimezone(pytz.timezone(config['timezone']))

      update_config(int(guild_id), 'premium.subscribed_at', updatedAt)
      return { 'status': 'success' }, 200

    return { 'error': 'subscription data not found' }, 400

  # Handle the invoice.paid event
  # if event['type'] == 'invoice.paid':
  #   print('invoice paid event received')
  #   invoice = event['data']['object']

  #   with open('invoice_paid.json', 'w') as f:
  #     json.dump(invoice, f, indent=2)

  # Handle the invoice.payment_failed event
  # if event['type'] == 'invoice.payment_failed':
  #   print('invoice payment failed event received')
  #   invoice = event['data']['object']

  #   with open('invoice_payment_failed.json', 'w') as f:
  #     json.dump(invoice, f, indent=2)

  return {'status': 'error'}


class guild_models:
  def __init__(self, guild=None):
    super().__init__()
    self.guild: discord.Guild = guild

  @property
  def roles(self):
    roles = []
    for role in self.guild.roles:
      roles.append({
        'id': role.id,
        'name': role.name,
        'color': role.color,
        'permissions': role.permissions.value,
        'position': role.position,
        'disabled': role.position >= self.guild.me.top_role.position,
      })

    roles.sort(key=lambda x: x['position'], reverse=True)
    return roles

  @property
  def channels(self):
    text_channels = []
    voice = [channel for channel in self.guild.voice_channels]
    categories = [category for category in self.guild.categories]

    for channel in self.guild.text_channels:
      text_channels.append({
        'type': 'text',
        'id': channel.id,
        'name': channel.name,
        'position': channel.position,
        'can_send': channel.permissions_for(self.guild.me).send_messages,
      })

    def sortFn(chan):
      return chan.position

    text_channels.sort(key=lambda x: x['position'], reverse=False)
    voice.sort(key=sortFn)
    categories.sort(key=sortFn)
    return {"text": text_channels, "voice": voice, "categories": categories}

  @property
  def emojis(self):
    emojis = [emoji for emoji in self.guild.emojis]
    return emojis

  @property
  def isPremium(self):
    premiumStatus = False
    data = get_server_config(self.guild, True)

    premiumStatus = data['premium']['status']
    return premiumStatus

@bot.event
async def on_ready():
  print(f'We have logged in as {bot.user}')
  # bot.get_channel(1110277292124536953).send('Bot on vercel is online')

def run_app():
  app.run(host='0.0.0.0', port=8000)
async def keep_alive():
  Thread(target=run_app).start()

if __name__ == "__main__":
  bot.run(BOT_TOKEN)