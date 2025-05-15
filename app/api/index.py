from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import os
import json
from datetime import datetime
import uuid
import hashlib
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generate a secure secret key

# Simple file-based databases
TASKS_FILE = os.path.join(os.path.dirname(__file__), 'tasks.json')
USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')

# Helper functions for data access
def get_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return []

def save_tasks(tasks):
    with open(TASKS_FILE, 'w') as f:
        json.dump(tasks, f, indent=2)

def get_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return []

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_by_username(username):
    users = get_users()
    for user in users:
        if user['username'] == username:
            return user
    return None

def is_logged_in():
    return 'user_id' in session

# Routes for authentication
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validate input
        if not username or not password:
            flash('Username and password are required')
            return redirect(url_for('register'))
        
        # Check if username already exists
        if get_user_by_username(username):
            flash('Username already exists')
            return redirect(url_for('register'))
        
        # Create new user
        users = get_users()
        new_user = {
            'id': str(uuid.uuid4()),
            'username': username,
            'password': hash_password(password),
            'created_at': datetime.now().isoformat()
        }
        users.append(new_user)
        save_users(users)
        
        # Log the user in
        session['user_id'] = new_user['id']
        session['username'] = new_user['username']
        
        return redirect(url_for('home'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = get_user_by_username(username)
        
        if user and user['password'] == hash_password(password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Main routes
@app.route('/')
def home():
    if not is_logged_in():
        return redirect(url_for('login'))
    
    # Get only tasks for the current user
    all_tasks = get_tasks()
    user_tasks = [task for task in all_tasks if task.get('user_id') == session['user_id']]
    
    return render_template('index.html', tasks=user_tasks, username=session['username'])

@app.route('/tasks', methods=['GET'])
def get_all_tasks():
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    
    all_tasks = get_tasks()
    user_tasks = [task for task in all_tasks if task.get('user_id') == session['user_id']]
    
    return jsonify(user_tasks)

@app.route('/tasks', methods=['POST'])
def create_task():
    if not is_logged_in():
        return redirect(url_for('login'))
    
    tasks = get_tasks()
    data = request.form
    
    new_task = {
        'id': str(uuid.uuid4()),
        'user_id': session['user_id'],  # Associate task with current user
        'title': data.get('title', ''),
        'description': data.get('description', ''),
        'status': data.get('status', 'pending'),
        'created_at': datetime.now().isoformat()
    }
    
    tasks.append(new_task)
    save_tasks(tasks)
    
    return redirect(url_for('home'))

@app.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    
    tasks = get_tasks()
    task = next((t for t in tasks if t['id'] == task_id and t.get('user_id') == session['user_id']), None)
    
    if task:
        return jsonify(task)
    return jsonify({'error': 'Task not found'}), 404

@app.route('/tasks/<task_id>', methods=['PUT', 'POST'])
def update_task(task_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    
    tasks = get_tasks()
    task_index = next((i for i, t in enumerate(tasks) if t['id'] == task_id and t.get('user_id') == session['user_id']), None)
    
    if task_index is not None:
        data = request.form
        
        tasks[task_index]['title'] = data.get('title', tasks[task_index]['title'])
        tasks[task_index]['description'] = data.get('description', tasks[task_index]['description'])
        tasks[task_index]['status'] = data.get('status', tasks[task_index]['status'])
        
        save_tasks(tasks)
        return redirect(url_for('home'))
    
    return jsonify({'error': 'Task not found'}), 404

@app.route('/tasks/<task_id>/delete', methods=['POST'])
def delete_task(task_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    
    tasks = get_tasks()
    task_index = next((i for i, t in enumerate(tasks) if t['id'] == task_id and t.get('user_id') == session['user_id']), None)
    
    if task_index is not None:
        del tasks[task_index]
        save_tasks(tasks)
        return redirect(url_for('home'))
    
    return jsonify({'error': 'Task not found'}), 404

# For local development
if __name__ == '__main__':
    app.run(debug=True)

