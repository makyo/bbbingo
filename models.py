from bbbingo import db


class User(db.Document):
    username = db.StringField()
    email = db.StringField()
    password = db.StringField()
    cards = db.ListField(db.ReferenceField('Card'))
    plays = db.ListField(db.ReferenceField('Play'))


class Card(db.Document):
    name = db.StringField()
    owner = db.ReferenceField(User)
    values = db.ListField(db.IntField())
    free_space = db.BooleanField(default=True)
    free_space_text = db.StringField()

    # public|loggedin|unlisted|private
    privacy = db.StringField(default='public')
    playable = db.StringField(default='yes')  # yes|owner|no
    plays = db.EmbeddedDocumentListField('Play')


class Play(db.Document):
    owner = db.ReferenceField(User)
    card = db.ReferenceField(Card)
    description = db.StringField()
    order = db.ListField(db.IntField())
    solution = db.ListField(db.BooleanField())
