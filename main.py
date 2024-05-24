from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, validators
from wtforms.validators import DataRequired
import requests


# CREATE DB
class DB(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=DB)


# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    ranking: Mapped[int] = mapped_column(Integer, nullable=False)
    review: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String, nullable=False)


class EditForm(FlaskForm):
    rating = StringField('Your rating out of 10 e.g. 7.5', validators=[validators.Length(min=0, max=3), DataRequired()])
    review = StringField('Your review', validators=[validators.Length(min=0, max=250), DataRequired()])
    submit = SubmitField('Done')


class AddForm(FlaskForm):
    title = StringField('Movie title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db.init_app(app)
Bootstrap5(app)


@app.route("/")
def home():
    with app.app_context():
        all_movies = db.session.execute(db.select(Movie).order_by(Movie.rating)).scalars().all()[::-1]
        for i in range(len(all_movies)):
            update_rating(movie_id=all_movies[i].id, new_ranking=(i + 1))

        return render_template("index.html", movies=all_movies)


@app.route("/edit/<int:movie_id>", methods=['GET', 'POST'])
def edit(movie_id):
    form = EditForm()
    if request.method == "POST" and form.validate():
        with app.app_context():
            current_movie = db.get_or_404(Movie, movie_id)
            current_movie.rating = form.rating.data
            current_movie.review = form.review.data
            db.session.commit()
            return redirect(url_for('home'))
    return render_template("edit.html", form=form)


@app.route('/delete/<int:movie_id>', methods=["GET", "POST"])
def delete(movie_id):
    with app.app_context():
        current_movie = db.get_or_404(Movie, movie_id)
        db.session.delete(current_movie)
        db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddForm()
    if request.method == "POST" and form.validate():
        url = f"https://api.themoviedb.org/3/search/movie?query={form.title.data}&include_adult=true&language=en"
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0MzlkMDc3Yjc1ZjJhZjU5M2VhNzBjOTVjM2JmYjAzNCIsInN1YiI6IjY2NTA1NzI0NmUwYWNmMTI2NTZiMGZkMCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.07QEwOvWjcCqRxnlcv-YyDqo7zyfQKG8xGCySa1y9Dg"
        }

        response = requests.get(url, headers=headers)
        movies_from_api = response.json()["results"]
        return render_template("select.html", movies=movies_from_api)

    return render_template("add.html", form=form)


@app.route("/add_selected")
def add_selected():
    new_movie = Movie(
        title=request.args.get('title'),
        year=request.args.get('year').split("-")[0],
        description=request.args.get('description'),
        rating="{:.1f}".format(float(request.args.get('rating'))),
        ranking=0,
        review="blank",
        img_url=f"https://image.tmdb.org/t/p/w500{request.args.get('img_url')}",
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('home'))


def update_rating(movie_id, new_ranking):
    movie_to_update = db.get_or_404(Movie, movie_id)
    movie_to_update.ranking = new_ranking
    db.session.commit()


if __name__ == '__main__':
    app.run(debug=True)
