from flask import Blueprint, render_template, request, flash, redirect, url_for, session, request, jsonify

bp = Blueprint("user", __name__)

@bp.route('/user_page', methods=['GET', 'POST'])
def user_page():
    current_loans = get_currently_loaned_books()
    user_history = get_user_history()
    current_requests = get_requested_books()

    if user_history is None or current_loans is None or user_history is None or current_requests is None:
        return redirect('/login')

    return render_template('user_page.html', user_history=user_history, current_loans=current_loans,
                           current_requests=current_requests)


@bp.route('/return_book/<int:copy_id>', methods=['POST'])
def return_book(copy_id):
    db_cur = get_db_cursor()

    user_id = session.get('user_id')

    if user_id is None:
        return redirect('/login')

    db_cur.execute("""
    SELECT return_book(%s)
    """, (copy_id,))

    flash('Book returned successfully!', 'success')

    return redirect('/user_page')


@bp.route('/extend_loan/<int:book_id>/<int:copy_id>', methods=['POST'])
def extend_loan(book_id, copy_id):
    db_cur = get_db_cursor()

    user_id = session.get('user_id')

    if user_id is None:
        return redirect('/login')

    db_cur.execute("""
    SELECT extend_loan(%s, %s, %s)
    """, (user_id, book_id, copy_id))
    flash('Loan extended!', 'success')

    return redirect('/user_page')

@bp.route('/save_rating', methods=['POST'])
def save_rating():
    book_id = request.form['book_id']
    rating = request.form['rating']

    db_cur = get_db_cursor()

    user_id = session.get('user_id')

    if user_id is None:
        return redirect('/login')

    db_cur.execute("""
        SELECT * FROM Reviews WHERE user_id = %s AND book_id = %s
        """, (user_id, book_id,))

    existing_review = db_cur.fetchone()

    if existing_review:
        flash('You have already reviewed this book.', 'warning')
    else:

        db_cur.execute("""
            SELECT insert_review(%s, %s, %s)
            """, (user_id, book_id, rating))

        flash('Review submitted!', 'success')

    return redirect('/user_page')


@bp.route('/cancel_request/<int:book_id>', methods=['POST'])
def cancel_request(book_id):
    db_cur = get_db_cursor()

    user_id = session.get('user_id')

    if user_id is None:
        return redirect('/login')

    db_cur.execute("""
        DELETE FROM Book_queue
        WHERE user_id = %s AND book_id = %s 
        """, (user_id, book_id))

    flash('Cancelled request!', 'success')

    return redirect('/user_page')


def get_user_history():
    db_cur = get_db_cursor()

    user_id = session.get('user_id')

    if user_id is None:
        return None

    db_cur.execute("""
    SELECT h.history_id, b.book_cover, b.title, h.loan_date, h.return_date, b.id
    FROM History h
    INNER JOIN Book b ON h.book_id = b.id
    WHERE h.user_id = %s
    """, (user_id,))

    user_history = db_cur.fetchall()

    fixed_user_history = []
    for loan in user_history:
        book_id = loan[5]
        average_rating = get_average_rating(book_id)
        if average_rating:
            book = loan + (average_rating,)
            fixed_user_history.append(book)
        else:
            fixed_user_history.append(loan + ("N/A",))

    return fixed_user_history


def get_currently_loaned_books():
    db_cur = get_db_cursor()

    user_id = session.get('user_id')

    if user_id is None:
        return None

    db_cur.execute("""
    SELECT bs.book_id, bs.copy_id, b.book_cover, b.title, bs.loan_start, bs.loan_end
    FROM Book_status bs
    INNER JOIN Book b ON bs.book_id = b.id
    WHERE bs.user_id = %s
    """, (user_id,))

    current_loans = db_cur.fetchall()

    fixed_current_loans = []
    for loan in current_loans:
        book_id = loan[0]
        average_rating = get_average_rating(book_id)
        if average_rating:
            book = loan + (average_rating,)
            fixed_current_loans.append(book)
        else:
            fixed_current_loans.append(loan + ("N/A",))

    return fixed_current_loans


def get_requested_books():
    db_cur = get_db_cursor()

    user_id = session.get('user_id')

    if user_id is None:
        return None

    db_cur.execute("""
        SELECT bq.book_id, bq.user_id, bq.place_in_queue, b.book_cover, b.title
        FROM book_queue bq
        INNER JOIN Book b ON bq.book_id = b.id
        WHERE bq.user_id = %s
        """, (user_id,))

    requests = db_cur.fetchall()

    fixed_requested_books = []
    for loan in requests:
        book_id = loan[0]
        average_rating = get_average_rating(book_id)
        if average_rating:
            book = loan + (average_rating,)
            fixed_requested_books.append(book)
        else:
            fixed_requested_books.append(loan + ("N/A",))

    return fixed_requested_books


def get_average_rating(book_id):
    db_cur = get_db_cursor()
    db_cur.execute("""
    SELECT AVG(rating) AS average_rating
    FROM Reviews
    WHERE book_id = %s
    """, (book_id,))
    result = db_cur.fetchone()
    average_rating = result[0] if result else None

    if average_rating is not None:
        average_rating = round(average_rating, 1)

    return average_rating


def get_db_cursor():
    from app import get_db_connection
    db = get_db_connection()
    db.autocommit = True
    db_cur = db.cursor()
    return db_cur
