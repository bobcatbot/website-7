from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/about')
def about():
    return 'About'

# Define a flag to check if the app is running
app_started = False

def run_app():
  global app_started
  app_started = True  # Update the flag when the app starts
  app.run(host='0.0.0.0', port=8000)
run_app()