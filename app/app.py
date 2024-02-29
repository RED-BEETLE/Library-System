from flask import Flask, render_template, request, redirect
import psycopg2
from auth import bp as auth
from search import bp as search
from user import bp as user
from genres import bp as genres
from ages import bp as ages

app = Flask(__name__, template_folder='../templates', static_folder='../templates/static')
app.secret_key = '12askjnfkjdfn'

def get_db_connection():
    connection = psycopg2.connect(
        database="bookManager",
        user="a",
        password="1234",
        host="localhost",
        port='5432'
    )
    return connection


con = get_db_connection()
cursor = con.cursor()

app.register_blueprint(auth)
app.register_blueprint(search)
app.register_blueprint(user)
app.register_blueprint(genres)
app.register_blueprint(ages)


@app.route("/")
def home():

    cursor.execute(
        "SELECT id, title, book_cover FROM Book ORDER BY published DESC LIMIT 12"
    )
    new_books = cursor.fetchall()

    cursor.execute(
        """SELECT b.id, b.title, b.book_cover, ROUND(rew.r, 1)
            FROM Book AS b, (SELECT book_id, AVG(rating) AS r 
            FROM reviews GROUP BY book_id ORDER BY r DESC LIMIT 12) 
            AS rew WHERE rew.book_id = b.id ORDER BY rew.r DESC
            """
    )
    best_reviewed_books = cursor.fetchall()

    cursor.execute("SELECT id, title, book_cover FROM Book ORDER BY random() LIMIT 12")
    random_books = cursor.fetchall()

    return render_template('home.html', new_books=new_books, best_reviewed_books=best_reviewed_books, random_books=random_books)


@app.route("/user_page")
def user_page():
    return render_template('user_page.html')

@app.route("/login")
def login():
    return render_template('login.html')

@app.route("/register")
def register():
    return render_template('register.html')
