from bbbingo import db


class User(db.Document):
    username = db.StringField()
    password = db.StringField()
    cards = db.ListField(db.ReferenceField(Card))


class Card(db.Document):
    name = db.StringField()
    owner = db.ReferenceField(User)
    values = db.ListField(db.ListField(db.IntegerField()))
    privacy = db.StringField()  # public|unlisted|private
    playable = db.StringField()  # yes|owner|no
    solves = db.EmbeddedDocumentListField(Solve)


class Solve(db.Document):
    owner = db.ReferenceField(User)
    card = db.ReferenceField(Card)
    description = db.StringField()
    solution = db.ListField(db.ListField(db.BooleanField()))
    solution_string = db.StringField()
