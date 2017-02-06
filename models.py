from bbbingo import db


class User(db.Document):
    username = db.StringField(unique=True)
    email = db.StringField()
    password = db.StringField()
    cards = db.ListField(db.ReferenceField('Card'))
    plays = db.ListField(db.ReferenceField('Play'))


class Card(db.Document):
    slug = db.StringField(unique=True)
    name = db.StringField()
    owner = db.ReferenceField(User)
    category = db.StringField(default='uncategorized')
    values = db.ListField(db.StringField(default=''))
    free_space = db.BooleanField(default=True)
    free_space_text = db.StringField()
    # public|loggedin|unlisted|private
    privacy = db.StringField(default='public')
    playable = db.StringField(default='yes')  # yes|owner|no
    plays = db.ListField(db.ReferenceField('Play'))

    meta = {
        'ordering': ['-id'],
    }

    def is_playable(self, user):
        if self.is_viewable(user):
            if self.playable == 'yes':
                return True
            if self.playable == 'owner' and self.owner == user:
                return True
        return False

    def is_viewable(self, user):
        if self.privacy == 'private' and user != self.owner:
            return False
        if self.privacy == 'loggedin' and not user:
            return False
        return True


class Play(db.Document):
    slug = db.StringField(unique=True)
    owner = db.ReferenceField(User)
    card = db.ReferenceField(Card)
    description = db.StringField()
    order = db.ListField(db.IntField())
    solution = db.ListField(db.BooleanField())

    meta = {
        'ordering': ['-id'],
    }
