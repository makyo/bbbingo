from base64 import (
    b16encode,
    urlsafe_b64decode,
    urlsafe_b64encode,
)
import bcrypt
import hashlib
import os
import random

from flask import (
    Flask,
    Response,
    abort,
    flash,
    g,
    jsonify,
    session,
    redirect,
    render_template,
    request,
)
from flask_mongoengine import MongoEngine


app = Flask(__name__)
app.config["MONGODB_SETTINGS"] = {'DB': 'bbbingo'}
app.config["SECRET_KEY"] = os.urandom(12)
app.config["DEBUG"] = True
app.url_map.strict_slashes = False
db = MongoEngine(app)

# Older python compat - db has to be defined first.
import models


@app.before_request
def before_request():
    g.user = user_from_session()
    if request.method == "POST":
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)


# Template helpers
def generate_csrf_token():
    if not app.config['TESTING'] and '_csrf_token' not in session:
        session['_csrf_token'] = hashlib.sha1(os.urandom(40)).hexdigest()
    return session.get('_csrf_token', '')


def _enslug(model):
    return urlsafe_b64encode(model.id.binary).decode()


def _deslug(id):
    return b16encode(urlsafe_b64decode(id)).decode().lower()


def cachebust():
    return hashlib.sha1(os.urandom(40)).hexdigest() \
        if app.config['DEBUG'] else 0


def fake_wrap(text, width, lines):
    parts = re.split(r'\s+', text)
    result = []
    while len(parts) > 0:
        part = ''
        while len(part) < width:
            part = ' '.join([part, parts.pop(0)])
        result.append(part.strip())
    if len(result) > lines:
        result = result[0:lines - 1]
        result.append('...')
    return result


def generate_slot_svg(text):
    return '<text>{}</text>'.format(text)


app.jinja_env.globals['csrf_token'] = generate_csrf_token
app.jinja_env.globals['slug'] = _enslug
app.jinja_env.globals['cachebust'] = cachebust
app.jinja_env.globals['slot_text'] = generate_slot_svg


def user_from_session():
    if session.get('user'):
        return models.User.objects.get(id=session.get('user')['_id']['$oid'])
    else:
        return None


@app.route('/', methods=['GET'])
def front():
    return render_template('front.html',
                           title='Hey there~')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        try:
            user = models.User.objects.get(
                username=request.form.get('username'))
            if bcrypt.checkpw(request.form.get('password').encode('utf-8'),
                              user.password.encode('utf-8')):
                session['user'] = user
                return redirect("/")
            else:
                raise
        except:
            flash(
                u'There was an error trying to log in, yo. Sorry, try again?',
                'error')
    return render_template('login.html',
                           title='Go on, log in')


@app.route('/logout', methods=['GET'])
def logout():
    del session['user']
    g.user = None
    flash('Boom, logged out. Come back soon!', 'success')


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form.get('username', '')
            if len(username) < 1 or len(username) > 32:
                flash('Gotta enter a username. 1-32 chars plz.', 'error')
                raise
            password = request.form.get('password')
            if len(password) < 8 or password != \
                    request.form.get('confirm_password'):
                flash('Passwords: >7 chars, must match confirmation!', 'error')
                raise
            user = models.User(
                username=username,
                password=bcrypt.hashpw(
                    password.encode(), bcrypt.gensalt()).decode(),
                email=request.form.get('email'))
            user.save()
            session['user'] = user
            return redirect('/')
        except Exception as e:
            flash(
                u'There was an error trying to register, yo. Sorry, '
                'try again? {}'.format(e),
                'error')
    return render_template('register.html',
                           title='Whoa, I want in on this')


@app.route('/~<username>', methods=['GET','POST'])
def profile(username):
    user = models.User.objects.get(username=username)
    return render_template('profile.html',
                           title='Hey hey, look it\'s {}'.format(
                               user.username),
                           user=user)


@app.route('/build', methods=['GET'])
def build_card():
    if session.get('user'):
        card = models.Card(
            owner=g.user,
            privacy='public',
            playable='yes')
        card.save()
        g.user.cards.append(card)
        g.user.save()
        return redirect('/build/bbb{}'.format(_enslug(card)))
    else:
        return redirect('/login')


@app.route('/build/bbb<card_id>', methods=['GET'])
def edit_card(card_id):
    if session.get('user'):
        card = models.Card.objects.get(pk__endswith=_deslug(card_id))
        if not card:
            abort(404)
        if g.user != card.owner:
            abort(403)
        return render_template('build.html',
                               title="Building {}! Woo!".format(
                                   'card' if card.name is None else card.name),
                               card=card)
    else:
        return redirect('/login')


@app.route('/accept/card/bbb<card_id>', methods=['PUT'])
def accept_card_data(card_id):
    if session.get('user'):
        try:
            card = models.Card.objects.get(pk__endswith=_deslug(card_id))
            if not card:
                abort(404)
            if g.user != card.owner:
                abort(403)
            slot = request.form.get('slot')
            text = request.form.get('text')
            card.free_space = request.form.get('free_space', False)
            card.free_space_text= request.form.get('free_space_text',
                                                   card.free_space_text)
            if slot == 'name':
                card.name = text
            elif slot == 'privacy':
                card.privacy = text
            elif slot == 'playable':
                card.playable = text
            else:
                card.values[int(slot)] = text
            card.save()
            return '{"status": "success"}'
        except Exception as e:
            return jsonify({
                "status": "failure",
                "message": str(e),
            })
    else:
        abort(403)


@app.route('/play/bbb<card_id>', methods=['GET'])
def play_card(card_id):
    if session.get('user'):
        card = models.Card.objects.get(pk=_deslug(card_id))
        order = list(range(1, 25 if card.free_space else 26))
        random.shuffle(order)
        play = models.Play(
            owner=session.get('user'),
            card=card,
            order=order)
        play.save()
        g.user.plays.append(play)
        g.user.save()
        return redirect('/play/bbb{}/{}'.format(card_id, _enslug(play)))
    else:
        return redirect('/login')


@app.route('/play/bbb<card_id>/<play_id>', methods=['GET'])
def edit_play(card_id, play_id):
    if session.get('user'):
        card = models.Card.objects.get(pk__endswith=_deslug(card_id))
        play = models.Play.objects.get(pk__endswith=_deslug(play_id))
        if not card or not play:
            abort(404)
        if g.user != play.owner:
            abort(403)
        return render_template('play.html',
                               play=play,
                               card=card)
    else:
        return redirect('/login')


@app.route('/accept/play/<play_id>', methods=['PUT'])
def accept_play_data(play_id):
    if session.get('user'):
        try:
            play = models.Play.objects.get(pk__endswith=_deslug(play_id))
            if not play:
                abort(404)
            if g.user != play.owner:
                abort(403)
            slot = request.form.get('slot')
            text = request.form.get('text')
            if slot == 'description':
                play.description = text
            else:
                play.values[int(slot)] = text is not None
            play.save()
            return '{"status": "success"}'
        except Exception as e:
            return jsonify({
                "status": "failure",
                "message": str(e),
            })
    else:
        abort(403)


@app.route('/bbb<card_id>/<play_id>', methods=['GET'])
def view_play(card_id, play_id):
    card = models.Card.objects.get(pk__endswith=_deslug(card_id))
    play = models.Play.objects.get(pk__endswith=_deslug(play_id))
    return render_template('view_play.html',
                           card=card,
                           play=play)


@app.route('/0x<card_id>/<play_id>.<format>', methods=['GET'])
def export_play(card_id, play_id, format):
    card = models.Card.objects.get(pk__endswith=_deslug(card_id))
    play = models.Play.objects.get(pk__endswith=_deslug(play_id))
    if format == 'svg':
        contents = render_template('card_embed.svg',
                                   card=card,
                                   play=play)
        if not request.args.get('embed', False):
            svg = render_template('card_standalone.svg',
                                  contents=contents)
        else:
            svg = contents
        return Response(svg, mimetype='image/svg+xml')
    abort(404)


@app.route('/bbb<card_id>.<format>', methods=['GET'])
def export_card(card_id, format):
    card = models.Card.objects.get(pk__endswith=_deslug(card_id))
    contents = render_template('card_embed.svg',
                               card=card)
    if not request.args.get('embed', False):
        svg = render_template('card_standalone.svg',
                              contents=contents)
    else:
        svg = contents
    return Response(svg, mimetype='image/svg+xml')


@app.route('/bbb<card_id>', methods=['GET'])
def view_card(card_id):
    card = models.Card.objects.get(pk__endswith=_deslug(card_id))
    if card.privacy == 'private' and g.user != card.owner:
        abort(403)
    if card.privacy == 'loggedin' and not session.get('user'):
        abort(403)
    return render_template('view_card.html',
                           card=card)


if __name__ == '__main__':
    app.secret_key = 'Development key'
    app.config['DEBUG'] = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run()
