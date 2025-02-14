from flask import Flask, send_from_directory
import os
from threading import Thread

app = Flask(__name__)

@app.route('/')
def serve_game():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

def run_server():
    port = int(os.environ.get('PORT', 5000))
    app.run(
        host='127.0.0.1',  # Только локальные подключения
        port=port
    )

def start_server():
    server_thread = Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start() 