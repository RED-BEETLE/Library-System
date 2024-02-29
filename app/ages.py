from flask import Blueprint, render_template, request, flash, redirect, url_for, session

bp = Blueprint('ages', __name__)

@bp.route('/0-3')
def zero_to_three ():
    ages = "0 - 3"
    age = [0, 1, 2]
    books = get_ages_and_books(age)
    return render_template('ages.html', ages=ages, books=books)


@bp.route('/3-6')
def three_to_six():
    ages = "3 - 6"
    age = [3, 4, 5]
    books = get_ages_and_books(age)
    return render_template('ages.html', ages=ages, books=books)


@bp.route('/6-9')
def six_to_nine():
    ages = "6 - 9"
    age = [6, 7, 8]
    books = get_ages_and_books(age)
    return render_template('ages.html', ages=ages, books=books)


@bp.route('/9-12')
def nine_to_twelve():
    ages = "9 - 12"
    age = [9, 10, 11]
    books = get_ages_and_books(age)
    return render_template('ages.html', ages=ages, books=books)


@bp.route('/young_adult')
def young_adult():
    ages = "Young Adult"
    from app import get_db_connection
    db = get_db_connection()
    db.autocommit = True
    cursor = db.cursor()
    cursor.execute(
        """	SELECT title, book_cover, id 
        	FROM Book 
            WHERE min_age = %s OR min_age = %s OR min_age = %s OR min_age = %s OR min_age = %s 
            ORDER BY RANDOM() LIMIT 15""", (12, 13, 14, 15, 16, )
    )
    books = cursor.fetchall()
    return render_template('ages.html', ages=ages, books=books)


@bp.route('/mature')
def mature():
    ages = "Mature"
    from app import get_db_connection
    db = get_db_connection()
    db.autocommit = True
    cursor = db.cursor()
    cursor.execute(
        "SELECT title, book_cover, id FROM Book WHERE min_age = %s OR min_age = %s ORDER BY RANDOM() LIMIT 15", (17, 18, )
    )
    books = cursor.fetchall()
    
    return render_template('ages.html', ages=ages, books=books)


def get_ages_and_books(age):
    from app import get_db_connection
    db = get_db_connection()
    db.autocommit = True
    cursor = db.cursor()

    cursor.execute(
        "SELECT title, book_cover, id FROM Book WHERE min_age = %s OR min_age = %s OR min_age = %s ORDER BY RANDOM() LIMIT 15", (age[0], age[1], age[2], )
    )
    books = cursor.fetchall()

    return books
