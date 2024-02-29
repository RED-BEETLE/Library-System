from flask import Blueprint, render_template, request, flash, redirect, url_for, session
import bcrypt

bp = Blueprint('search', __name__, url_prefix='/search')


@bp.route('/search', methods=['GET', 'POST'])
def search():
    books_found = []
    if request.method == 'POST':
        keyword = request.form['keyword']
        from app import get_db_connection
        db = get_db_connection()
        db.autocommit = True
        db_cur = db.cursor()
        error = None

        if not keyword:
            error = 'Keyword is required'

        if error is None:
            db_cur.execute(
                """SELECT DISTINCT b.id, b.title, b.book_cover, ROUND(r.rew, 1) 
                    FROM Book AS b, 
                    (SELECT book_id, AVG(rating) AS rew FROM Reviews 
                    GROUP BY book_id ORDER BY rew DESC LIMIT 12) as r 
                    WHERE b.title ILIKE %s;""",
                ('%' + keyword + '%',),
            )
            books_found = db_cur.fetchall()
            db_cur.close()
        else:
            flash(error, 'danger')
    return render_template('search.html', books=books_found)


@bp.route('/show_book', methods=['GET', 'POST'])
def show_book():
    book_found = []
    is_available = False
    if request.method == 'GET':
        id = request.args.get('id')
        from app import get_db_connection
        db = get_db_connection()
        db.autocommit = True
        db_cur = db.cursor()
        error = None
        is_requested = False

        if session.get("user_id") is not None:
             # was book already requested by the user
            db_cur.execute(
                "SELECT * FROM book_queue where book_id = %s and user_id = %s;",
                (id, session.get("user_id")),
            )
            requests = db_cur.fetchone()
            is_requested = requests is not None

        if not id:
            error = 'ID is required'

        if error is None:
            # get details about book
            db_cur.execute(
                """SELECT b.*, g.genre, a.author 
                    FROM Book AS b, Genres AS g, Authors AS a 
                    WHERE b.author_id = a.author_id 
                    AND b.genre_id = g.genre_id AND b.id = %s;
                    """,
                (id,),
            )
            book_found = db_cur.fetchone()

            # is book available?
            db_cur.execute(
                "SELECT check_if_copy_is_available(%s);",
                (id,),
            )
            result = db_cur.fetchone()[0]
            is_available = result is not None
            db_cur.close()
        else:
            flash(error, 'danger')
    return render_template('book_overview.html', book=book_found, is_available=is_available, is_requested=is_requested)


@bp.route('/loan', methods=['GET', 'POST'])
def loan():
    if request.method == 'GET':
        id = request.args.get('bid')
        from app import get_db_connection
        db = get_db_connection()
        db.autocommit = True
        db_cur = db.cursor()
        error = None

        if session.get("user_id") is None:
            print("Not logged in")
            return redirect('/user_page')

        if not id:
            error = 'ID is required'

        if error is None:
            # get details about book
            db_cur.execute(
                "SELECT loan_book(%s,%s)",
                (session['user_id'], id,),
            )
            status = db_cur.fetchone()
            print(status)
            db_cur.close()
        else:
            flash(error, 'danger')
    return redirect('/user_page')


@bp.route('/recommend', methods=['GET', 'POST'])
def recommend():
    if request.method == 'GET':
        id = request.args.get('bid')
        from app import get_db_connection
        db = get_db_connection()
        db.autocommit = True
        db_cur = db.cursor()
        error = None

        if not id:
            error = 'ID is required'

        if error is None:
            # get embedding of current book
            db_cur.execute(
                """SELECT embedding
                    FROM Book_embedding AS e
                    WHERE e.book_id = %s;""",
                (id,),
            )
            embedding = db_cur.fetchone()

            # find similar book
            sql_find_closest = """SELECT book_id FROM book_embedding WHERE book_id <> %s 
                ORDER BY euclidean_distance(embedding, %s) LIMIT 1;"""
            db_cur.execute(sql_find_closest, (id, embedding,))
            closest_sentence = db_cur.fetchone()
            db_cur.close()
        else:
            flash(error, 'danger')
    return redirect('/search/show_book?id=' + str(closest_sentence[0]))
