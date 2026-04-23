from flask import Flask, render_template, request, redirect, session, url_for
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["university_lost_found"]
users_collection = db["users"]

# -------------------------------
# Home Route
# -------------------------------
@app.route('/')
def home():
    return redirect('/login')

# -------------------------------
# Register Route
# -------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        # Check if user already exists
        if users_collection.find_one({"email": email}):
            return "User already exists!"

        users_collection.insert_one({
            "name": name,
            "email": email,
            "password": password,
            "role": "user"
        })

        return redirect('/login')

    return render_template('register.html')

# -------------------------------
# Login Route
# -------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = users_collection.find_one({"email": email})

        if user and check_password_hash(user['password'], password):
            session['user'] = user['name']
            session['role'] = user['role']
            return redirect('/dashboard')
        else:
            return "Invalid Email or Password!"

    return render_template('login.html')

# -------------------------------
# Dashboard Route
# -------------------------------
@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        return render_template('dashboard.html', user=session['user'], role=session['role'])
    return redirect('/login')

# -------------------------------
# Logout Route
# -------------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# -------------------------------
# Run App
# -------------------------------
if __name__ == '__main__':
    app.run(debug=True)