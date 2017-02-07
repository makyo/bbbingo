import bcrypt
import cgi
import hashlib
import os
import random
from random_words import (
    RandomNicknames,
    RandomWords,
)
import re

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
rw = RandomWords()
rn = RandomNicknames()

# Older python compat - db has to be defined first.
import models


def user_from_session():
    if session.get('user'):
        return models.User.objects.get(
            username=session.get('user')['username'])
    else:
        return None


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


def cachebust():
    return hashlib.sha1(os.urandom(40)).hexdigest() \
        if app.config['DEBUG'] else 0


def fake_wrap(text, width, lines):
    parts = re.split(r'\s+', text)
    result = []
    while len(parts) > 0:
        part = ''
        while parts and len(part) < width:
            if len(part) > 0 and len(part) + len(parts[0]) > int(width * 1.5):
                break
            part = ' '.join([part, parts.pop(0)])
        result.append(part.strip())
    if len(result) > lines:
        result = result[0:lines - 1]
        result.append('...')
    return result


def generate_slot_svg(text):
    slot_text = ''
    if not text:
        return slot_text
    lines = fake_wrap(text, 10, 6)
    i = 1
    offset = 45 - (len(lines) * 15) / 2
    for line in lines:
        slot_text += '<text x="50" y="{}" text-anchor="middle">' \
            '{}</text>'.format(offset + 15 * i, cgi.escape(line))
        i += 1
    return slot_text


app.jinja_env.globals['csrf_token'] = generate_csrf_token
app.jinja_env.globals['cachebust'] = cachebust
app.jinja_env.globals['slot_text'] = generate_slot_svg


ALLOWED_CATEGORIES = (
    'uncategorized',
    'funny',
    'kinky',
    'snarky',
    'treasture hunt',
    'convention',
    'special occasion',
    'personal',
)


@app.route('/', methods=['GET'])
def front():
    recent_cards = models.Card.objects.filter(
        privacy='public').order_by('-id')[:10]
    recent_plays = []
    for play in models.Play.objects.all().order_by('-id').select_related():
        if play.card.privacy == 'public':
            recent_plays.append(play)
        if len(recent_plays) == 10:
            break
    return render_template('front.html',
                           title='Hey there~',
                           cards=recent_cards,
                           plays=recent_plays,
                           categories=ALLOWED_CATEGORIES)


@app.route('/conduct', methods=['GET'])
def conduct():
    return render_template('coc.html', title='Code of Conduct')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        try:
            user = models.User.objects.get(
                username=request.form.get('username'))
            if bcrypt.checkpw(request.form.get('password').encode('utf-8'),
                              user.password.encode('utf-8')):
                session['user'] = user
                return redirect(request.args.get('next', '/'))
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
    try:
        del session['user']
        g.user = None
    except:
        pass
    flash('Boom, logged out. Come back soon!', 'success')
    return redirect('/')


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
    cards = models.Card.objects.filter(owner=user)
    plays = models.Play.objects.filter(owner=user).select_related()
    return render_template('profile.html',
                           title='Hey hey, look it\'s {}'.format(
                               user.username),
                           user=user,
                           cards=cards,
                           plays=plays)


@app.route('/category/<category>', methods=['GET'])
@app.route('/category/<category>/<int:page>', methods=['GET'])
def category_list(category, page=1):
    privacy_levels = ['public']
    if session.get('user'):
        privacy_levels.append('loggedin')
    if page == 0:
        page = 1
    start = 20 * (page - 1)
    cards = models.Card.objects.filter(
        privacy__in=privacy_levels, category=category)[start:start + 20]
    try:
        test_next = models.Card.objects.filter(
            privacy__in=privacy_levels, category=category)[start + 21]
        has_next = test_next is not None
    except IndexError:
        has_next = False
    return render_template('category.html',
                           title='Ooh, the {} category'.format(category),
                           category=category,
                           categories=ALLOWED_CATEGORIES,
                           has_next=has_next,
                           page=page,
                           cards=cards)


@app.route('/build', methods=['GET'])
def build_card():
    if session.get('user'):
        card = models.Card(
            slug='-'.join(rw.random_words(count=4)),
            owner=g.user,
            privacy='public',
            playable='yes',
            values= [''] * 25)
        card.save()
        card.short_id = models.short_id(card)
        card.save()
        g.user.cards.append(card)
        g.user.save()
        return redirect('/build/{}'.format(card.slug))
    else:
        return redirect('/login')


@app.route('/build/<card_id>', methods=['GET'])
def edit_card(card_id):
    if session.get('user'):
        card = models.Card.objects.get(slug=card_id)
        if not card:
            abort(404)
        if g.user != card.owner:
            abort(403)
        return render_template('build.html',
                               title="Building {}! Woo!".format(
                                   card.slug if card.name is None
                                   else card.name),
                               card=card,
                               allowed_categories=ALLOWED_CATEGORIES)
    else:
        return redirect('/login?next=/build/{}'.format(card_id))


@app.route('/accept/card/<card_id>', methods=['POST'])
def accept_card_data(card_id):
    if session.get('user'):
        generate_csrf_token()
        try:
            card = models.Card.objects.get(slug=card_id)
            if not card:
                return jsonify({
                    'status': 'failure',
                    'message': 'not found',
                    'csrf_token': session.get('_csrf_token'),
                })
            if g.user != card.owner:
                return jsonify({
                    'status': 'failure',
                    'message': 'permission denied: card belongs to {}, '
                               'you are {}'.format(
                                   card.owner.username, g.owner.username),
                    'csrf_token': session.get('_csrf_token'),
                })
            slot = request.form.get('slot')
            text = request.form.get('text')[:256]
            if slot == 'name':
                card.name = text
            elif slot == 'category':
                card.category = text
            elif slot == 'privacy':
                card.privacy = text
            elif slot == 'playable':
                card.playable = text
            elif slot == 'free_space':
                card.free_space = text == 'True'
            elif slot == 'free_space_text':
                card.free_space_text = text
            else:
                card.values[int(slot)] = text
            card.save()
            return jsonify({
                'status': 'success',
                'csrf_token': session.get('_csrf_token'),
            })
        except Exception as e:
            return jsonify({
                'status': 'failure',
                'message': str(e),
                'csrf_token': session.get('_csrf_token'),
            })
    else:
        abort(403)


@app.route('/delete/<card_id>', methods=['GET', 'POST'])
def delete_card(card_id):
    card = models.Card.objects.get(slug=card_id)
    if request.method == 'POST':
        if card.owner.username != g.user.username:
            abort(403)
        if session['delete_word'] == request.form.get('delete_word'):
            card.delete()
            return redirect('/~{}'.format(g.user.username))
        else:
            flash('That aint the word, yo!', 'error')
    session['delete_word'] = rw.random_word()
    return render_template('delete.html',
                           title='Let go of your feelings, '
                               '{}...'.format(card.name),
                           card=card)



@app.route('/play/<card_id>', methods=['GET'])
def play_card(card_id):
    if session.get('user'):
        card = models.Card.objects.get(slug=card_id)
        order = list(range(0, 24 if card.free_space else 25))
        random.shuffle(order)
        if card.free_space:
            order[order.index(12)] = 24
            order = order[:12] + [12] + order[12:]

        parts = [
            rn.random_nick(gender='f').lower(),
            rn.random_nick(gender='m').lower(),
            rn.random_nick(gender='u').lower(),
        ]
        random.shuffle(parts)
        play = models.Play(
            slug='-'.join(parts),
            owner=g.user,
            card=card,
            order=order,
            solution=[False] * 25)
        play.save()
        play.short_id = models.short_id(play)
        play.save()
        card.plays.append(play)
        card.save()
        g.user.plays.append(play)
        g.user.save()
        return redirect('/play/{}/{}'.format(card.slug, play.slug))
    else:
        return redirect('/login?next=/play/{}'.format(card_id))


@app.route('/play/<card_id>/<play_id>', methods=['GET'])
def edit_play(card_id, play_id):
    if session.get('user'):
        card = models.Card.objects.get(slug=card_id)
        play = models.Play.objects.get(slug=play_id)
        if not card or not play:
            abort(404)
        if g.user != play.owner:
            abort(403)
        return render_template('play.html',
                               play=play,
                               card=card,
                               title='{}! Playtime!'.format(
                                   card.slug if card.name is None
                                   else card.name))
    else:
        return redirect('/login?next=/play/{}/{}'.format(card_id, play_id))


@app.route('/accept/play/<play_id>', methods=['POST'])
def accept_play_data(play_id):
    if session.get('user'):
        generate_csrf_token()
        try:
            play = models.Play.objects.get(slug=play_id)
            if not play:
                return jsonify({
                    'status': 'failure',
                    'message': 'play not found',
                    'csrf_token': session.get('_csrf_token'),
                })
            if g.user != play.owner:
                return jsonify({
                    'status': 'failure',
                    'message': 'permission denied: play belongs to {}, '
                               'you are {}'.format(
                                   play.owner.username, g.owner.username),
                    'csrf_token': session.get('_csrf_token'),
                })
            slot = request.form.get('slot')
            text = request.form.get('text')[:256]
            if slot == 'description':
                play.description = text
            else:
                play.solution[int(slot)] = text == 'mark'
            play.save()
            return jsonify({
                'status': 'success',
                'csrf_token': session.get('_csrf_token'),
            })
        except Exception as e:
            return jsonify({
                "status": "failure",
                "message": str(e),
                'csrf_token': session.get('_csrf_token'),
            })
    else:
        abort(403)


@app.route('/delete/<card_id>/<play_id>', methods=['GET', 'POST'])
def delete_play(card_id, play_id):
    play = models.Play.objects.get(slug=play_id).select_related()
    if request.method == 'POST':
        if card_id != play.card.slug:
            abort(404)
        if play.owner.username != g.user.username:
            abort(403)
        if session['delete_word'] == request.form.get('delete_word'):
            play.delete()
            return redirect('/~{}', g.user.username)
        else:
            flash('That aint the word, yo!', 'error')
    session['delete_word'] = rw.random_word()
    return render_template('delete.html',
                           title='Let go of your feelings, '
                               '{}...'.format(play.description[:35]),
                           play=play)


@app.route('/<part1>-<part2>-<part3>-<part4>/<play_id>', methods=['GET'])
def view_play(part1, part2, part3, part4, play_id):
    card = models.Card.objects.get(
        slug='-'.join([part1, part2, part3, part4]))
    if not card.is_viewable(g.user):
        abort(403)
    play = models.Play.objects.get(slug=play_id)
    return render_template('view_play.html',
                           card=card,
                           play=play,
                           title='{}\'s play of {}'.format(
                               play.owner.username,
                               card.slug if card.name is None \
                                   else card.name))


@app.route('/<part1>-<part2>-<part3>-<part4>/<play_id>.<format>', methods=['GET'])
def export_play(part1, part2, part3, part4, play_id, format):
    card = models.Card.objects.get(
        slug='-'.join([part1, part2, part3, part4]))
    if not card.is_viewable(g.user):
        abort(403)
    play = models.Play.objects.get(slug=play_id)
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


@app.route('/<part1>-<part2>-<part3>-<part4>.<format>', methods=['GET'])
def export_card(part1, part2, part3, part4, format):
    card = models.Card.objects.get(
        slug='-'.join([part1, part2, part3, part4]))
    if not card.is_viewable(g.user):
        abort(403)
    contents = render_template('card_embed.svg',
                               card=card)
    if not request.args.get('embed', False):
        svg = render_template('card_standalone.svg',
                              contents=contents)
    else:
        svg = contents
    return Response(svg, mimetype='image/svg+xml')


@app.route('/<part1>-<part2>-<part3>-<part4>', methods=['GET'])
def view_card(part1, part2, part3, part4):
    card = models.Card.objects.get(
        slug='-'.join([part1, part2, part3, part4])).select_related()
    if not card.is_viewable(g.user):
        abort(403)
    return render_template('view_card.html',
                           card=card,
                           title='Neat, it\'s {}\'s card {}'.format(
                               card.owner.username,
                               card.slug if card.name is None else card.name))


@app.route('/-<short_card_id>', methods=['GET'])
def short_view_card(short_card_id):
    card = models.Card.objects.get(short_id=short_card_id)
    return redirect('/{}'.format(card.slug))


@app.route('/!<short_play_id>', methods=['GET'])
def short_view_play(short_play_id):
    play = models.Play.objects.get(short_id=short_play_id)
    return redirect('/{}/{}'.format(play.card.slug, play.slug))


if __name__ == '__main__':
    app.secret_key = 'Development key'
    app.config['DEBUG'] = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run()
