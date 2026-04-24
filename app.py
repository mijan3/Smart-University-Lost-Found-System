from flask import Flask, render_template, request, redirect, session, send_from_directory
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = "secret123"

app.config['UPLOAD_FOLDER'] = 'uploads'

client = MongoClient("mongodb://localhost:27017/")
db = client["university_lost_found"]

users_collection = db["users"]
items_collection = db["items"]

# ---------------- HOME ----------------
@app.route('/')
def home():
    return redirect('/login')

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        if users_collection.find_one({"email": request.form['email']}):
            return "User already exists"

        users_collection.insert_one({
            "name": request.form['name'],
            "email": request.form['email'],
            "password": generate_password_hash(request.form['password']),
            "role": "user"
        })
        return redirect('/login')

    return render_template('register.html')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = users_collection.find_one({"email": request.form['email']})

        if user and check_password_hash(user['password'], request.form['password']):
            if user['role'] != request.form['role']:
                return "Wrong role selected"

            session['user'] = user['name']
            session['role'] = user['role']

            return redirect('/admin' if user['role']=='admin' else '/dashboard')

        return "Invalid login"

    return render_template('login.html')

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        return render_template('dashboard.html', user=session['user'])
    return redirect('/login')

# ---------------- ADMIN ----------------
@app.route('/admin')
def admin():
    if session.get('role') == 'admin':
        return render_template('admin.html', user=session['user'])
    return redirect('/login')

# ---------------- ADD ITEM ----------------
@app.route('/add-item', methods=['GET','POST'])
def add_item():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        files = request.files.getlist('images')
        images = []

        for file in files:
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                images.append(filename)

        items_collection.insert_one({
            "title": request.form['title'],
            "description": request.form['description'],
            "status": request.form['status'],
            "images": images,
            "created_by": session['user'],
            "approved": False,
            "comments": [],
            "claimed_by": None
        })

        return redirect('/dashboard')

    return render_template('add_item.html')

# ---------------- VIEW ITEMS ----------------
@app.route('/items')
def items():
    status = request.args.get('status')

    query = {"approved": True}
    if status:
        query["status"] = status

    items = list(items_collection.find(query))
    return render_template('view_items.html', items=items)

# ---------------- COMMENT ----------------
@app.route('/comment/<id>', methods=['POST'])
def comment(id):
    items_collection.update_one(
        {"_id": ObjectId(id)},
        {"$push": {"comments": {
            "user": session['user'],
            "text": request.form['comment']
        }}}
    )
    return redirect('/items')

# ---------------- CLAIM ----------------
@app.route('/claim/<id>')
def claim(id):
    item = items_collection.find_one({"_id": ObjectId(id)})

    if item.get("claimed_by"):
        return "Already claimed"

    items_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"claimed_by": session['user']}}
    )

    return redirect('/items')

# ---------------- UPLOADS ----------------
@app.route('/uploads/<filename>')
def uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ---------------- ADMIN ITEMS ----------------
@app.route('/admin/items')
def admin_items():
    if session.get('role') == 'admin':
        items = list(items_collection.find())
        return render_template('admin_items.html', items=items)
    return redirect('/login')

# ---------------- APPROVE ----------------
@app.route('/approve/<id>')
def approve(id):
    items_collection.update_one({"_id": ObjectId(id)}, {"$set": {"approved": True}})
    return redirect('/admin/items')

# ---------------- DELETE ----------------
@app.route('/delete/<id>')
def delete(id):
    items_collection.delete_one({"_id": ObjectId(id)})
    return redirect('/admin/items')

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)