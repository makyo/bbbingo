from flask import Flask
from flask_mongoengine import MongoEngine


app = Flask(__name__)
app.config["MONGODB_SETTINGS"] = {'DB': 'bbbingo'}
app.config["SECRET_KEY"] = os.urandom(12)
app.config["DEBUG"] = False
db = MongoEngine(app)


@app.route('/', methods=['GET'])
def front():
    pass


@app.route('/login', methods=['GET','POST'])
def login():
    pass


@app.route('/register', methods=['GET','POST'])
def register():
    pass


@app.route('/~<username>', methods=['GET','POST'])
def profile(username):
    pass


@app.route('/build/<card_id>', methods=['GET','POST'])
def build_card(card_id):
    pass


@app.route('/play/<card_id>', methods=['GET','PUT'])
def play_card(card_id):
    pass


@app.route('/<card_id>/<play_id>', methods=['GET'])
def view_play(card_id, play_id):
    pass


@app.route('/<card_id>/<play_id>.<format>', methods=['GET'])
def view_play(card_id, play_id, format):
    pass


@app.route('/<card_id>.<format>', methods=['GET'])
def export_card(card_id, format):
    pass


@app.route('/<card_id>', methods=['GET'])
def view_card(card_id):
    pass


if __name__ == '__main__':
    app.secret_key = 'Development key'
    app.debug = True
    app.run()
