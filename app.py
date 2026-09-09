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


@app.route('/')
def index():
    users = data_manager.get_users()
    return render_template('index.html', users=users)


@app.route('/users', methods=['POST'])
def create_user():
    name = request.form.get('name')
    if name:
        data_manager.create_user(name)
    return redirect(url_for('index'))


@app.route('/users/<int:user_id>/movies', methods=['GET'])
def show_user_movies(user_id):
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('index'))
    movies = data_manager.get_movies(user_id)
    return render_template('movies.html', user=user, movies=movies)


@app.route('/users/<int:user_id>/movies', methods=['POST'])
def add_movie_to_user(user_id):
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
            director=data.get('Director'),
            year=int(data.get('Year', 0)) if data.get('Year') else None,
            poster_url=data.get('Poster'),
            user_id=user_id
        )
        data_manager.add_movie(movie)

    return redirect(url_for('show_user_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/update', methods=['POST'])
def update_movie(user_id, movie_id):
    new_title = request.form.get('title')
    if new_title:
        data_manager.update_movie(movie_id, new_title)
    return redirect(url_for('show_user_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/delete', methods=['POST'])
def delete_movie(user_id, movie_id):
    data_manager.delete_movie(movie_id)
    return redirect(url_for('show_user_movies', user_id=user_id))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)