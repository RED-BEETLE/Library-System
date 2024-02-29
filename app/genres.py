from flask import Blueprint, render_template, request, flash, redirect, url_for, session

bp = Blueprint('genres', __name__)

@bp.route('/fantasy')
def fantasy():
    result = get_genre_and_books(1)
    top_books = top_ranked_books(1)
    return render_template('genres.html', genre=result[0], books=result[1], top_books=top_books)


@bp.route('/romance')
def romance():
    result = get_genre_and_books(4)
    top_books = top_ranked_books(4)
    return render_template('genres.html', genre=result[0], books=result[1], top_books=top_books)

@bp.route('/sci-fi')
def scifi():
    result = get_genre_and_books(2)
    top_books = top_ranked_books(2)
    return render_template('genres.html', genre=result[0], books=result[1], top_books=top_books)


@bp.route('/mystery')
def mystery():
    result = get_genre_and_books(5)
    top_books = top_ranked_books(5)
    return render_template('genres.html', genre=result[0], books=result[1], top_books=top_books)


@bp.route('/thriller')
def thriller():
    result = get_genre_and_books(6)
    top_books = top_ranked_books(6)
    return render_template('genres.html', genre=result[0], books=result[1], top_books=top_books)


@bp.route('/adventure')
def adventure():
    result = get_genre_and_books(3)
    top_books = top_ranked_books(3)
    return render_template('genres.html', genre=result[0], books=result[1], top_books=top_books)


def get_genre_and_books(genre_id):
    from app import get_db_connection
    db = get_db_connection()
    db.autocommit = True
    cursor = db.cursor()

    cursor.execute(
        "SELECT genre FROM genres WHERE genre_id = %s", (genre_id, )
    )
    genre = cursor.fetchall()
    genre = genre[0][0]

    cursor.execute(
        "SELECT title, book_cover, id FROM Book WHERE genre_id = %s ORDER BY RANDOM() LIMIT 12", (genre_id, )
    )
    books = cursor.fetchall()

    return genre, books


def top_ranked_books(genre_id):
    from app import get_db_connection
    db = get_db_connection()
    db.autocommit = True
    cursor = db.cursor()

    cursor.execute(
        """ SELECT b.title, b.book_cover, b.id, ROUND(rew.r, 1) 
            FROM Book AS b, (SELECT rev.book_id, AVG(rev.rating) AS r 
                FROM reviews AS rev, book AS b
                WHERE b.genre_id = %s AND b.id = rev.book_id
                GROUP BY book_id 
                ORDER BY r DESC LIMIT 12) 
                AS rew 
            WHERE rew.book_id = b.id 
            ORDER BY rew.r DESC""", (genre_id, )
    )
    books = cursor.fetchall()

    return books
