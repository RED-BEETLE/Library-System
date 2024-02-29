from flask import Blueprint, render_template, request, flash, redirect, url_for, session
import bcrypt

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        birthdate = request.form['birthdate']
        role = request.form['role']
        from app import get_db_connection
        db = get_db_connection()
        db.autocommit = True
        db_cur = db.cursor()
        error = None

        if not email:
            error = 'Email is required'
        elif not username:
            error = 'Username is required'
        elif not password:
            error = 'Password is required'
        elif not birthdate:
            error = "Birthday is required"
        elif not role:
            error = "Role is required"

        if error is None:
            try:
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                pw_hash = hashed_password.decode('utf-8')
                db_cur.execute(
                    "INSERT INTO Client (id, user_name, user_password, birthdate, user_role) VALUES (%s, %s, %s, %s, %s)",
                    (email, username, pw_hash, birthdate, role)
                )

                flash('Registration successful!', 'success')
                return redirect('/login')

            except:
                error = f"User {username} is already registered."

        flash(error, 'danger')

    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        from app import get_db_connection
        db = get_db_connection()
        db.autocommit = True
        db_cur = db.cursor()
        error = None

        db_cur.execute("SELECT id, user_password FROM Client WHERE id = %s", (email,))
        user_data = db_cur.fetchone()

        if user_data:
            user_id = user_data[0]
            user_password = user_data[1]
        if not user_data:
            error = "Invalid email or password"
        elif bcrypt.checkpw(password.encode('utf-8'), user_password.encode()):
            session['user_id'] = user_id
            flash('Login successful!', 'success')
            return redirect('/user_page')
        else:
            error = "Invalid email or password"

        if error:
            flash(error, 'danger')
    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect('/login')

