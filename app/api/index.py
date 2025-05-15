from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import os
import json
from datetime import datetime
import uuid
import hashlib
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generate a secure secret key

# In-memory storage for development/demo purposes
# In production, you would use a database
USERS = []
TASKS = []

# Load initial data if files exist (for local development)
def load_initial_data():
    global USERS, TASKS
    
    # Try to load users
    if os.path.exists('app/api/users.json'):
        try:
            with open('app/api/users.json', 'r') as f:
                USERS = json.load(f)
        except:
            pass
    
    # Try to load tasks
    if os.path.exists('app/api/tasks.json'):
        try:
            with open('app/api/tasks.json', 'r') as f:
                TASKS = json.load(f)
        except:
            pass

# Load data on startup
load_initial_data()

# Helper functions
def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_by_username(username):
    for user in USERS:
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
        new_user = {
            'id': str(uuid.uuid4()),
            'username': username,
            'password': hash_password(password),
            'created_at': datetime.now().isoformat()
        }
        USERS.append(new_user)
        
        # Try to save to file (for local development)
        try:
            with open('app/api/users.json', 'w') as f:
                json.dump(USERS, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save users to file: {e}")
        
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
    user_tasks = [task for task in TASKS if task.get('user_id') == session['user_id']]
    
    return render_template('index.html', tasks=user_tasks, username=session['username'])

@app.route('/tasks', methods=['GET'])
def get_all_tasks():
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_tasks = [task for task in TASKS if task.get('user_id') == session['user_id']]
    
    return jsonify(user_tasks)

@app.route('/tasks', methods=['POST'])
def create_task():
    if not is_logged_in():
        return redirect(url_for('login'))
    
    data = request.form
    
    new_task = {
        'id': str(uuid.uuid4()),
        'user_id': session['user_id'],  # Associate task with current user
        'title': data.get('title', ''),
        'description': data.get('description', ''),
        'status': data.get('status', 'pending'),
        'created_at': datetime.now().isoformat()
    }
    
    TASKS.append(new_task)
    
    # Try to save to file (for local development)
    try:
        with open('app/api/tasks.json', 'w') as f:
            json.dump(TASKS, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save tasks to file: {e}")
    
    return redirect(url_for('home'))

@app.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    
    task = next((t for t in TASKS if t['id'] == task_id and t.get('user_id') == session['user_id']), None)
    
    if task:
        return jsonify(task)
    return jsonify({'error': 'Task not found'}), 404

@app.route('/tasks/<task_id>', methods=['PUT', 'POST'])
def update_task(task_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    
    task_index = next((i for i, t in enumerate(TASKS) if t['id'] == task_id and t.get('user_id') == session['user_id']), None)
    
    if task_index is not None:
        data = request.form
        
        TASKS[task_index]['title'] = data.get('title', TASKS[task_index]['title'])
        TASKS[task_index]['description'] = data.get('description', TASKS[task_index]['description'])
        TASKS[task_index]['status'] = data.get('status', TASKS[task_index]['status'])
        
        # Try to save to file (for local development)
        try:
            with open('app/api/tasks.json', 'w') as f:
                json.dump(TASKS, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save tasks to file: {e}")
        
        return redirect(url_for('home'))
    
    return jsonify({'error': 'Task not found'}), 404

@app.route('/tasks/<task_id>/delete', methods=['POST'])
def delete_task(task_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    
    task_index = next((i for i, t in enumerate(TASKS) if t['id'] == task_id and t.get('user_id') == session['user_id']), None)
    
    if task_index is not None:
        del TASKS[task_index]
        
        # Try to save to file (for local development)
        try:
            with open('app/api/tasks.json', 'w') as f:
                json.dump(TASKS, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save tasks to file: {e}")
        
        return redirect(url_for('home'))
    
    return jsonify({'error': 'Task not found'}), 404

# For local development
if __name__ == '__main__':
    app.run(debug=True)



