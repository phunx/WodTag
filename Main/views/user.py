from ..util import db
from ..models import *
import flask
import flask_login
import flask.views


## All Users
class Users(flask.views.MethodView):
    def get(self):
        users = session.query(User).all()
        pass

    def post(self):
        return Users.new_user()

    @staticmethod
    def new_user():
        if Users.validate_user_create() != 0:
            return flask.redirect(flask.url_for('user_create'))
        else:
            user = User(flask.request.form['username'], flask.request.form['password'])
            user_type = flask.request.form.get('user_type', '')
            if user_type == "owner":
                user.is_gym_owner = True
            db.session.add(user)
            db.session.commit()
            return flask.redirect(flask.url_for('index'))

    @staticmethod
    def validate_user_create():
        error = 0
        if flask.request.form['username'] == "":
            flask.flash("Username is required!", "error")
            error += 1
        elif flask.request.form['password'] == "" or flask.request.form['password2'] == "":
            flask.flash("Password is required!", "error")
            error += 1
        elif flask.request.form['password'] != flask.request.form['password2']:
            flask.flash("Passwords must match!", "error")
            error += 1
        user_type = flask.request.form.get('user_type', '')
        if not user_type:
            flask.flash("Define membership type!", "error")
            error += 1
        return error

    @staticmethod
    def owners_of_gym(gym_id):
        users = User.query.filter_by(owner_gym_id=gym_id).all()
        return flask.render_template('gym_owners.html', users=users)

    @staticmethod
    def members_of_gym(gym_id):
        users = User.query.filter_by(member_gym_id=id).all()
        return flask.render_template('gym_members.html', users=users)


## User CREATE View
class UserCreate(flask.views.MethodView):
    def get(self):
        return flask.render_template('user_create.html')


## User EDIT View
class UserEdit(flask.views.MethodView):
    def get(self, user_id):
        if user_id is not None:
            user = User.query.get(user_id)
            return flask.render_template('user_edit.html', user=user)
        else:
            return flask.render_template('404.html'), 404


## User DELETE View
class UserDelete(flask.views.MethodView):
    def get(self, user_id):
        pass


## User CRUD
class UserCRUD(flask.views.MethodView):
    def get(self, user_id):
        if user_id is not None and User.query.get(user_id) is not None:
            user = User.query.get(user_id)
            if user is not None:
                return flask.render_template('user.html', viewed_user=user, user=flask_login.current_user)
        return flask.render_template('404.html'), 404

    def post(self, user_id):
        method = flask.request.form.get('_method', '')
        if method == "PUT":
            return UserCRUD.edit_user(user_id)
        elif method == "DELETE":
            return UserCRUD.delete_user(user_id)
        else:
            return flask.render_template('404.html'), 404

    @staticmethod
    def edit_user(user_id):
        if UserCRUD.validate_user_edit() != 0:
            return flask.redirect(flask.url_for('user_edit', user_id=user_id))
        else:
            user = User.query.get(user_id)
            user.username = flask.request.form['username']
            db.session.add(user)
            db.session.commit()
            return flask.redirect(flask.url_for('user', user_id=user.id))

    @staticmethod
    def delete_user(user_id):
        pass

    @staticmethod
    def validate_user_edit():
        error = 0
        if flask.request.form['username'] == "":
            flask.flash("Username is required!", "error")
            error += 1
        return error