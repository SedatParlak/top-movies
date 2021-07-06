from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
from tmdbv3api import TMDb, Movie, Authentication
import os

USERNAME = os.environ.get("USERNAME")
PASSWORD = os.environ.get("PASSWORD")
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")

tmdb = TMDb()
tmdb.api_key = TMDB_API_KEY

auth = Authentication(username=USERNAME, password=PASSWORD)

tmdb.language = 'en'
tmdb.debug = True


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap(app)

db = SQLAlchemy(app)


class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.String, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(250))
    img_url = db.Column(db.String(250), nullable=False)


db.create_all()


class MovieForm(FlaskForm):
    rating = FloatField(label='Your Rating Out of 10 e.g. 7.5 : ',
                        validators=[DataRequired()], render_kw={"autofocus": True, "autocomplete": "off"})
    review = StringField(label='Your Review : ', validators=[DataRequired()],
                         render_kw={"autofocus": True, "autocomplete": "off"})
    submit = SubmitField(label="Done")


class AddForm(FlaskForm):
    title = StringField(label='Movie Title : ',
                        validators=[DataRequired()], render_kw={"autofocus": True, "autocomplete": "off"})
    submit = SubmitField(label="Search")


@app.route("/")
def home():
    all_movies = Movies.query.order_by(Movies.rating).all()

    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", all_movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = MovieForm()
    movie_id = request.args.get('id')
    movie = Movies.query.get(movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", form=form)


@app.route("/delete")
def delete():
    movie_id = request.args.get('id')
    movie_to_delete = Movies.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddForm()
    if form.validate_on_submit():
        add_movie = form.title.data
        movie = Movie()

        searching_movies = movie.search(add_movie)
        movie_list = list()
        for search in searching_movies:
            search["title"] = getattr(search, 'title', 'n/a')
            search["release_date"] = getattr(search, 'release_date', 'n/a')
            search["overview"] = getattr(search, 'overview', 'n/a')
            search["poster_path"] = getattr(search, 'poster_path', 'n/a')
            if search["poster_path"]:
                url = "https://image.tmdb.org/t/p/original" + search["poster_path"]
            else:
                search["poster_path"] = ""
            movie_list.append([search["title"], search["release_date"], url, search["overview"]])
        return render_template("select.html", movie_list=movie_list)
    return render_template("add.html", form=form)


@app.route("/find")
def find():
    movie_title = request.args.get('title')
    date = request.args.get('release_date')
    url = request.args.get('poster_path')
    movie_overview = request.args.get('overview')

    new_movie = Movies(
        title=movie_title,
        year=date,
        description=movie_overview,
        rating=None,
        ranking=None,
        review=None,
        img_url=url
    )

    db.session.add(new_movie)
    db.session.commit()

    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5000)
