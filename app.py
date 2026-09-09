from flask import Flask, render_template, request, redirect, url_for
from data_manager import DataManager
from models import db, Movie, User
import os
import requests

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'movies.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
data_manager = DataManager()

OMDB_API_KEY = '4f95cb28'
OMDB_URL = 'http://www.omdbapi.com/'


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


@app.route('/')
def index():
    try:
        users = data_manager.get_users()
        return render_template('index.html', users=users)
    except Exception as e:
        print(f"Error in index: {str(e)}")
        return render_template('500.html'), 500


@app.route('/users', methods=['POST'])
def create_user():
    try:
        name = request.form.get('name')
        if name:
            data_manager.create_user(name)
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        return redirect(url_for('index'))


@app.route('/users/<int:user_id>/movies', methods=['GET'])
def show_user_movies(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return redirect(url_for('index'))
        movies = data_manager.get_movies(user_id)
        return render_template('movies.html', user=user, movies=movies)
    except Exception as e:
        print(f"Error showing movies: {str(e)}")
        return redirect(url_for('index'))


@app.route('/users/<int:user_id>/movies', methods=['POST'])
def add_movie_to_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return redirect(url_for('index'))

        movie_title = request.form.get('movie_title')

        if not movie_title:
            return redirect(url_for('show_user_movies', user_id=user_id))

        params = {
            'apikey': OMDB_API_KEY,
            't': movie_title
        }

        response = requests.get(OMDB_URL, params=params)
        data = response.json()

        if data.get('Response') == 'True':
            movie = Movie(
                name=data.get('Title'),
                director=data.get('Director', 'N/A'),
                year=int(data.get('Year', 0)) if data.get('Year') else None,
                poster_url=data.get('Poster', 'N/A'),
                user_id=user_id
            )
            data_manager.add_movie(movie)

        return redirect(url_for('show_user_movies', user_id=user_id))
    except Exception as e:
        print(f"Error adding movie: {str(e)}")
        return redirect(url_for('show_user_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/update', methods=['POST'])
def update_movie(user_id, movie_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return redirect(url_for('index'))

        new_title = request.form.get('title')
        if new_title:
            data_manager.update_movie(movie_id, new_title)
        return redirect(url_for('show_user_movies', user_id=user_id))
    except Exception as e:
        print(f"Error updating movie: {str(e)}")
        return redirect(url_for('show_user_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/delete', methods=['POST'])
def delete_movie(user_id, movie_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return redirect(url_for('index'))

        data_manager.delete_movie(movie_id)
        return redirect(url_for('show_user_movies', user_id=user_id))
    except Exception as e:
        print(f"Error deleting movie: {str(e)}")
        return redirect(url_for('show_user_movies', user_id=user_id))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)