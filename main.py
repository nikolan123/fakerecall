from flask import Flask, render_template, send_from_directory, abort, jsonify, request, redirect, url_for
import os
import time
import threading
import json
from datetime import datetime, timezone, timedelta
import random
from humanize import naturalsize
from glob import glob

app = Flask(__name__)

SERVER_PORT = '1212'
DATA_DIR = 'data'

# heartbeat stuff
heartbeat_active = False
last_heartbeat_time = time.time() - 10

def monitor_heartbeat():
    global heartbeat_active, last_heartbeat_time
    while True:
        if time.time() - last_heartbeat_time > 10:
            heartbeat_active = False
        else:
            heartbeat_active = True
        time.sleep(1)

monitor_thread = threading.Thread(target=monitor_heartbeat)
monitor_thread.daemon = True
monitor_thread.start()

@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    global last_heartbeat_time
    last_heartbeat_time = time.time()
    return "Heartbeat received", 200
# ---

@app.route('/')
def index():
    folders_data = []

    try:
        folders = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
    except FileNotFoundError:
        folders = []

    folders.sort(key=lambda x: int(x), reverse=True)

    for folder in folders:
        activity_path = os.path.join(DATA_DIR, folder, 'activity.json')
        try:
            with open(activity_path, 'r') as file:
                activity_data = json.load(file)
                primary = activity_data.get("focused", "N/A")
        except (FileNotFoundError, json.JSONDecodeError):
            primary = "N/A"

        folders_data.append((folder, primary))
    
    try:
        img_folder = random.choice(folders)
    except IndexError:
        img_folder = ""
    
    file_size = naturalsize(sum(os.path.getsize(x) for x in glob('./data/**', recursive=True)))
    capture_status = "currently capturing" if heartbeat_active == True else "not capturing"
    
    return render_template('homepage.html', folders_data=folders_data, img_folder=img_folder, capture_amount=len(folders_data), file_size=file_size, capture_status=capture_status)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    if not query:
        return redirect(url_for('index'))

    results = []

    try:
        folders = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
    except FileNotFoundError:
        folders = []

    for folder in folders:
        activity_path = os.path.join(DATA_DIR, folder, 'activity.json')
        try:
            with open(activity_path, 'r') as file:
                activity_data = json.load(file)
                text = activity_data.get("text", "")
                if query.lower() in text.lower():
                    primary = activity_data.get("focused", "N/A")
                    results.append((folder, primary))
        except (FileNotFoundError, json.JSONDecodeError):
            continue

    try:
        img_folder = random.choice(folders)
    except IndexError:
        img_folder = ""
    
    print(img_folder)
    
    return render_template('search.html', folders_data=results, img_folder=img_folder, capture_amount=len(results))

@app.route('/folder')
def folder():
    os.startfile(os.path.normpath("data"))
    return redirect("/")

@app.route('/<folder>/<filename>')
def serve_file(folder, filename):
    folder_path = os.path.join(DATA_DIR, folder)
    if not os.path.isdir(folder_path):
        abort(404)
    return send_from_directory(folder_path, filename)

@app.template_filter('to_datetime')
def to_datetime_filter(unix_timestamp):
    return datetime.fromtimestamp(int(unix_timestamp), tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

if __name__ == '__main__':
    app.run(debug=True, port='1212')
