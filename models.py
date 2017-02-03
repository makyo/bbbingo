from bbbingo import db


class User(db.Document):
    username = db.StringField()
    email = db.StringField()
    password = db.StringField()
    cards = db.ListField(db.ReferenceField('Card'))


class Card(db.Document):
    name = db.StringField()
    owner = db.ReferenceField(User)
    values = db.ListField(db.IntField())
    pin_frees_space = db.BooleanField()
    privacy = db.StringField()  # public|unlisted|private
    playable = db.StringField()  # yes|owner|no
    solves = db.EmbeddedDocumentListField('Solve')


class Solve(db.Document):
    owner = db.ReferenceField(User)
    card = db.ReferenceField(Card)
    description = db.StringField()
    order = db.ListField(db.StringField())
    order_string = db.StringField()
    solution = db.ListField(db.BooleanField())
    solution_string = db.StringField()
