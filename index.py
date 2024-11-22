from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/about')
def about():
    return 'About'


def run_app():
  app.run(host='0.0.0.0', port=8000)
# run_app()