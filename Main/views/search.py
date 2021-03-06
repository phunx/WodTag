import datetime
from ..models import *
from sqlalchemy.sql import and_, or_
from flask.ext.login import login_required
import flask
import flask_login
import flask.views


class SearchView(flask.views.MethodView):
    @login_required
    def get(self):
        return flask.render_template('search.html', user=flask_login.current_user)

    @login_required
    def post(self):
        original_radio = flask.request.form.get('optionsRadios')
        original_from_date = flask.request.form.get('from_date')
        original_to_date = flask.request.form.get('to_date')
        original_tags = flask.request.form.getlist('tags[]')
        pr_only = flask.request.form.get('prCheckbox')

        from_date = original_from_date
        if from_date == "":
            from_date = "1900-01-01"

        to_date = original_to_date
        if to_date == "":
            to_date = "9999-12-31"

        from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
        to_date = datetime.datetime.strptime(to_date, '%Y-%m-%d')
        tags = SearchView.fix_tags(original_tags)

        if from_date > to_date:
            flask.flash("From Date must come before To Date!", "error")
            results = None
        else:
            if original_radio == "user":
                results = SearchView.get_user_results(from_date, to_date, tags, pr_only)
            elif original_radio == "gym":
                results = SearchView.get_gym_results(from_date, to_date, tags, pr_only)
            elif original_radio == "followed":
                results = SearchView.get_followed_results(from_date, to_date, tags, pr_only)
            else:
                results = SearchView.get_all_results(from_date, to_date, tags, pr_only)

        return flask.render_template('search.html',
                                     results=results,
                                     tags=tags,
                                     radio=original_radio,
                                     from_date=original_from_date,
                                     to_date=original_to_date,
                                     prCheckbox=pr_only,
                                     user=flask_login.current_user)

    @staticmethod
    def fix_tags(tags):
        final_tags = ""
        for tag in tags[0].split(','):
            final_tags += str(tag.strip()) + ","
        return str(final_tags)[:-1]

    @staticmethod
    def get_user_results(from_date, to_date, tags, pr_only):
        user_part_results = WorkoutPartResult.query.join(WorkoutResult) \
                                             .filter(WorkoutResult.user_id == flask_login.current_user.id) \
                                             .join(Workout).filter(and_(Workout.post_date >= from_date,
                                                                       (Workout.post_date <= to_date)))
        return SearchView.get_workout_results(user_part_results.all(), tags, pr_only)

    @staticmethod
    def get_gym_results(from_date, to_date, tags, pr_only):
        gym_id = flask_login.current_user.member_of_gym.id
        gym_part_results = WorkoutPartResult.query.join(WorkoutResult).join(Workout) \
                                            .filter(Workout.gym_id == gym_id) \
                                            .filter(and_(Workout.post_date >= from_date,
                                                        (Workout.post_date <= to_date)))
        return SearchView.get_workout_results(gym_part_results.all(), tags, pr_only)

    @staticmethod
    def get_followed_results(from_date, to_date, tags, pr_only):
        followed_part_results = WorkoutPartResult.query.join(WorkoutResult) \
                                                 .join(Workout).filter(and_(Workout.post_date >= from_date,
                                                                           (Workout.post_date <= to_date)))
        followed_ids = [u.id for u in flask_login.current_user.follows]
        followed_parts = [part for part in followed_part_results.all() if part.workout_result.user_id in followed_ids]
        return SearchView.get_workout_results(followed_parts, tags, pr_only)

    @staticmethod
    def get_all_results(from_date, to_date, tags, pr_only):
        all_part_results = WorkoutPartResult.query.join(WorkoutResult).join(Workout) \
                                                  .filter(and_(Workout.post_date >= from_date,
                                                              (Workout.post_date <= to_date)))
        return SearchView.get_workout_results(all_part_results.all(), tags, pr_only)

    @staticmethod
    def get_workout_results(result_list, tags, pr_only):
        if pr_only:
            result_list = [part for part in result_list if part.pr == 1]
        if not tags or tags == "":
            final_results = set([part.workout_result for part in result_list])
        else:
            final_results = set([part.workout_result for part in result_list
                                 if set([tag.name for tag in part.part.tags]) & set(tags.split(', '))])
        return final_results