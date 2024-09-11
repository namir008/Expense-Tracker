import sqlite3
from flask import Flask, render_template, request, url_for, flash, redirect, session
from werkzeug.exceptions import abort
from contextlib import closing
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

xpense = Flask(__name__)
xpense.config.from_object(Config)


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


def execute_query(query, args=(), fetch_one=False):
    conn = get_db_connection()
    cursor = conn.execute(query, args)
    result = cursor.fetchone() if fetch_one else cursor.fetchall()
    conn.commit()
    cursor.close()  
    conn.close() 
    return result





@xpense.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('register'))
    else:
        query = 'SELECT * FROM spendings'
        spendings = execute_query(query,)
        return render_template('index.html', spendings=spendings)





def get_spending(spending_id):
    query = 'SELECT * FROM spendings WHERE id = ?'
    spending = execute_query(query, (spending_id,), fetch_one=True)

    if spending is None:
        abort(404)

    return spending




@xpense.route('/<int:spending_id>')
def spending(spending_id):
    spending = get_spending(spending_id)
    return render_template('spending.html', spending=spending)


@xpense.route('/debit', methods=('GET', 'POST'))
def debit():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!', 'error')
        else:
            try:
                execute_query('INSERT INTO spendings (title, content) VALUES (?, ?)', (title, content))
                flash('Debit successfully added!', 'success')
                return redirect(url_for('index'))
            except sqlite3.DatabaseError as e:
                flash(f"An error occurred: {e}", 'error')

    return render_template('debit.html')



@xpense.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    spending = get_spending(id)

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            try:
                execute_query('UPDATE spendings SET title = ?, content = ? WHERE id = ?', (title, content, id))
                return redirect(url_for('index'))
            except sqlite3.DatabaseError as e:
                flash(f"An error occurred: {e}")
    return render_template('edit.html', spending=spending)


@xpense.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    spending = get_spending(id)
    try:
        execute_query('DELETE FROM spendings WHERE id = ?', (id,))
        flash('"{}" was successfully deleted!'.format(spending['title']))
    except sqlite3.DatabaseError as e:
                flash(f"An error occurred: {e}")
    return redirect(url_for('index'))













@xpense.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")

        if not (username and password and email):
            return render_template("register.html", message="All fields are required.")

        hashed_password = generate_password_hash(password)

        # Check if user already exists
        existing_user = execute_query('SELECT * FROM users WHERE username = ?', (username,), fetch_one=True)
        if existing_user:
            return render_template("register.html", message="Username already exists.")

        # Store user data in the database
        execute_query('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', 
                      (username, email, hashed_password))
        
        return redirect(url_for("login"))

    return render_template("register.html")

@xpense.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = execute_query('SELECT * FROM users WHERE username = ?', (username,), fetch_one=True)

        if user and check_password_hash(user['password'], password):
            session["user_id"] = user['id']
            return redirect(url_for("index"))
        else:
            return render_template("login.html", message="Invalid username or password.")

    return render_template("login.html")

@xpense.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    xpense.run(debug=True)