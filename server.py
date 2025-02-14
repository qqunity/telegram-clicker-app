from flask import Flask, send_from_directory, request, jsonify
import os
from threading import Thread
from game_repository import GameRepository

app = Flask(__name__)
game_repo = GameRepository()

@app.route('/')
def serve_game():
    return send_from_directory('.', 'index.html')

@app.route('/api/get_user_data')
def get_user_data():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'score': 0, 'multiplier': 1})

    try:
        result = game_repo.get_user_score(user_id)
        if result:
            return jsonify({
                'score': result[0],
                'multiplier': result[1]
            })
        return jsonify({'score': 0, 'multiplier': 1})
    except Exception as e:
        print(f"Ошибка при получении данных: {e}")
        return jsonify({'score': 0, 'multiplier': 1})

@app.route('/api/save_user_data', methods=['POST'])
def save_user_data():
    print("\n=== Начало обработки save_user_data ===")
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'Нет данных'}), 400

        user_id = str(data.get('user_id'))
        score = int(data.get('score', 0))
        multiplier = int(data.get('multiplier', 1))

        if not user_id:
            return jsonify({'status': 'error', 'message': 'Отсутствует user_id'}), 400

        saved_data = game_repo.save_score(user_id, score, multiplier)
        
        return jsonify({
            'status': 'success',
            'data': {
                'user_id': saved_data[0],
                'score': saved_data[1],
                'multiplier': saved_data[2]
            }
        })
    except Exception as e:
        print(f"Ошибка при сохранении данных: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400
    finally:
        print("=== Конец обработки save_user_data ===")

@app.route('/api/test_db')
def test_db():
    conn = db.get_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'No database connection'}), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            return jsonify({'status': 'success', 'message': 'Database connection ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

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

if __name__ == '__main__':
    run_server() 