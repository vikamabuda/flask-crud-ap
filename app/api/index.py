from flask import Flask, request, jsonify, render_template, redirect, url_for
import os
import json
from datetime import datetime
import uuid

app = Flask(__name__)

# Simple file-based database
DB_FILE = os.path.join(os.path.dirname(__file__), 'tasks.json')

def get_tasks():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return []

def save_tasks(tasks):
    with open(DB_FILE, 'w') as f:
        json.dump(tasks, f, indent=2)

@app.route('/')
def home():
    tasks = get_tasks()
    return render_template('index.html', tasks=tasks)

@app.route('/tasks', methods=['GET'])
def get_all_tasks():
    return jsonify(get_tasks())

@app.route('/tasks', methods=['POST'])
def create_task():
    tasks = get_tasks()
    data = request.form
    
    new_task = {
        'id': str(uuid.uuid4()),
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
    tasks = get_tasks()
    task = next((t for t in tasks if t['id'] == task_id), None)
    
    if task:
        return jsonify(task)
    return jsonify({'error': 'Task not found'}), 404

@app.route('/tasks/<task_id>', methods=['PUT', 'POST'])
def update_task(task_id):
    tasks = get_tasks()
    task_index = next((i for i, t in enumerate(tasks) if t['id'] == task_id), None)
    
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
    tasks = get_tasks()
    task_index = next((i for i, t in enumerate(tasks) if t['id'] == task_id), None)
    
    if task_index is not None:
        del tasks[task_index]
        save_tasks(tasks)
        return redirect(url_for('home'))
    
    return jsonify({'error': 'Task not found'}), 404

# For local development
if __name__ == '__main__':
    app.run(debug=True)
