import hashlib
import os

from flask import (
    Flask,
    abort,
    flash,
    g,
    session,
    redirect,
    render_template,
    request,
)
from flask_mongoengine import MongoEngine


app = Flask(__name__)
app.config["MONGODB_SETTINGS"] = {'DB': 'bbbingo'}
app.config["SECRET_KEY"] = os.urandom(12)
app.config["DEBUG"] = False
db = MongoEngine(app)

@app.before_request
def before_request():
    if request.method == "POST":
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)


# Template helpers
def generate_csrf_token():
    if not app.config['TESTING'] and '_csrf_token' not in session:
        session['_csrf_token'] = hashlib.sha1(os.urandom(40)).hexdigest()
    return session.get('_csrf_token', '')


app.jinja_env.globals['csrf_token'] = generate_csrf_token


@app.route('/', methods=['GET'])
def front():
    return render_template('front.html',
                           title='Hey there~')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        pass
    return render_template('login.html',
                           title='Go on, log in')


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        pass
    return render_template('register.html',
                           title='Whoa, I want in on this')


@app.route('/~<username>', methods=['GET','POST'])
def profile(username):
    pass


@app.route('/build/0x<card_id>', methods=['GET','POST'])
def build_card(card_id):
    pass


@app.route('/play/0x<card_id>', methods=['GET','PUT'])
def play_card(card_id):
    pass


@app.route('/0x<card_id>/<play_id>', methods=['GET'])
def view_play(card_id, play_id):
    pass


@app.route('/0x<card_id>/<play_id>.<format>', methods=['GET'])
def export_play(card_id, play_id, format):
    pass


@app.route('/0x<card_id>.<format>', methods=['GET'])
def export_card(card_id, format):
    pass


@app.route('/0x<card_id>', methods=['GET'])
def view_card(card_id):
    pass


if __name__ == '__main__':
    app.secret_key = 'Development key'
    app.debug = True
    app.run()
