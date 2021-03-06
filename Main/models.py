from util import db, lm
from sqlalchemy.orm import relationship
from datetime import date
import hashlib
import random

###
# Many-to-many joiner table (WorkoutPart >--< Tag)
#
tag_part_association = db.Table('tag_part_association',
                                db.Column('part_id', db.Integer, db.ForeignKey('WorkoutPart.id')),
                                db.Column('tag_id', db.Integer, db.ForeignKey('Tag.id')))

###
# Many-to-many joiner table (WorkoutResult >---< Tag)
#
tag_result_association = db.Table('tag_result_association',
                                  db.Column('result_id', db.Integer, db.ForeignKey('WorkoutResult.id')),
                                  db.Column('tag_id', db.Integer, db.ForeignKey('Tag.id')))

###
# Joiner for User following (User >---< User)
user_follows_association = db.Table('user_follows_association',
                                    db.Column('following_user_id', db.Integer, db.ForeignKey('User.id'), primary_key=True),
                                    db.Column('followed_user_id', db.Integer, db.ForeignKey('User.id'), primary_key=True))


class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    password = db.Column(db.String(128))
    salt = db.Column(db.String(128))
    email = db.Column(db.String(128))
    is_gym_owner = db.Column(db.Boolean)
    follows = relationship('User', secondary=user_follows_association,
                           primaryjoin=id==user_follows_association.c.following_user_id,
                           secondaryjoin=id==user_follows_association.c.followed_user_id,
                           backref='followed_by')
    member_gym_id = db.Column(db.Integer, db.ForeignKey('Gym.id'))
    owner_gym_id = db.Column(db.Integer, db.ForeignKey('Gym.id'))
    weighins = relationship('WeighIn', backref="user", order_by='WeighIn.date.desc()')
    goals = relationship('Goal', backref='user')

    def __init__(self, username, password):
        self.username = username
        self.salt = hashlib.md5(str(random.random())).hexdigest()
        self.password = hashlib.sha1(password + self.salt).hexdigest()

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

@lm.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class Gym(db.Model):
    __tablename__ = 'Gym'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    description = db.Column(db.String(512))

    owners = relationship('User', backref='owns_gym', foreign_keys="User.owner_gym_id")
    members = relationship('User', backref='member_of_gym', foreign_keys="User.member_gym_id")
    template_workouts = relationship('Workout', backref='gym', order_by='Workout.post_date.desc()')

    def __init__(self, name, description):
        self.name = name
        self.description = description


###
# Weigh In for a user. Currently simple and contains only weight and date of
# weigh in. Could potentially contain %fat, blood pressue, and other body statistics
#
class WeighIn(db.Model):
    __tablename__ = 'WeighIn'
    id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Float)
    body_fat = db.Column(db.Float)
    muscle_mass = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'))
    date = db.Column(db.Date)

    def __init__(self, weight):
        self.weight = weight


###
# Acts as a template for workout results. Gyms create and own templated workouts,
# which can be used to generate user-specific results. Workout templates are made
# up of at least one part
#
class Workout(db.Model):
    __tablename__ = 'Workout'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    post_date = db.Column(db.DateTime)
    gym_id = db.Column(db.Integer, db.ForeignKey('Gym.id'))

    parts = relationship('WorkoutPart', backref='workout', order_by='WorkoutPart.order')
    results = relationship('WorkoutResult', backref='workout')

    def __init__(self, name):
        self.name = name


###
# Pieces of a workout. Workouts are generally made up of two or three parts
#
class WorkoutPart(db.Model):
    __tablename__ = 'WorkoutPart'
    id = db.Column(db.Integer, primary_key=True)

    description = db.Column(db.String(512))
    workout_id = db.Column(db.Integer, db.ForeignKey('Workout.id'))
    order = db.Column(db.String(64))
    uom = db.Column(db.String(128))

    def __init__(self, description):
        self.description = description


###
# Workout results are owned by users
#
class WorkoutResult(db.Model):
    __tablename__ = 'WorkoutResult'
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('User.id'))
    workout_id = db.Column(db.Integer, db.ForeignKey('Workout.id'))
    user = relationship('User', backref='results')
    parts = relationship('WorkoutPartResult', backref='workout_result', order_by='WorkoutPartResult.order')


###
# Workout part results are owned by WorkoutResults
#
class WorkoutPartResult(db.Model):
    __tablename__ = 'WorkoutPartResult'
    id = db.Column(db.Integer, primary_key=True)
    result = db.Column(db.String(128))
    details = db.Column(db.String(512))
    order = db.Column(db.String(64))
    pr = db.Column(db.Boolean)

    part_id = db.Column(db.Integer, db.ForeignKey('WorkoutPart.id'))
    part = relationship('WorkoutPart', backref='results')
    result_id = db.Column(db.Integer, db.ForeignKey('WorkoutResult.id'))

    def __init__(self, result):
        self.result = result


###
# Assigned directly to workout results by users or to workout parts by gyms
class Tag(db.Model):
    __tablename__ = 'Tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    parts = relationship('WorkoutPart', secondary=tag_part_association, backref='tags')
    results = relationship('WorkoutResult', secondary=tag_result_association, backref='tags')

    def __init__(self, name):
        self.name = name


class Goal(db.Model):
    __tablename__ = 'Goal'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    complete = db.Column(db.Boolean)
    active = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'))
    parts = relationship('GoalPart', backref='goal', order_by='GoalPart.date.desc()')

class GoalPart(db.Model):
    __tablename__ = 'GoalPart'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(256))
    date = db.Column(db.DateTime)
    part_id = db.Column(db.Integer, db.ForeignKey('Goal.id'))