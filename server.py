from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit
import random

# Flask 및 Flask-SocketIO 설정
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='eventlet')

# 게임 관련 변수 초기화
topics = ["과일", "동물", "나라", "영화", "색깔", "운동", "도시"]
players = {}
liar = None
topic = None
hints_submitted = 0  # 제출된 힌트 수 카운트
total_players = 4    # 참여할 플레이어 수
guesses_submitted = 0  # 추측한 플레이어 수
rooms = {}  # 방 목록을 저장하는 딕셔너리

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/room/<room_id>')
def room(room_id):
    return render_template('room.html', room_id=room_id)

@socketio.on('create_room')
def create_room(data):
    room_id = data['room_id']
    rooms[room_id] = {'players': [], 'ready': [], 'started': False}
    emit('room_created', room_id, broadcast=True)

@socketio.on('join_room')
def join_room(data):
    room_id = data['room_id']
    player_name = data['player_name']
    rooms[room_id]['players'].append(player_name)
    emit('player_joined', player_name, room=room_id)

@socketio.on('ready')
def player_ready(data):
    room_id = data['room_id']
    player_name = data['player_name']
    rooms[room_id]['ready'].append(player_name)

    # 모든 플레이어가 준비되었는지 확인
    if len(rooms[room_id]['ready']) == len(rooms[room_id]['players']):
        if len(rooms[room_id]['players']) >= 3:  # 3명 이상일 경우만 게임 시작
            emit('start_game', room_id, broadcast=True)

# @socketio.on('join_game')
# def handle_join_game(player_name):
#     global liar, topic, hints_submitted, guesses_submitted

#     # 새로운 플레이어를 플레이어 목록에 추가하고 소켓 ID 저장
#     players[request.sid] = player_name

#     # 모든 플레이어들에게 현재 방에 있는 플레이어 목록을 전송
#     emit('update_player_list', {'players': list(players.values())}, broadcast=True)

#     # 플레이어가 다 모이면 라이어와 주제를 설정
#     if len(players) == total_players:
#         liar = random.choice(list(players.values()))
#         topic = random.choice(topics)
#         hints_submitted = 0  # 힌트 제출 수 초기화
#         guesses_submitted = 0  # 추측 제출 수 초기화

#         print(f"라이어: {liar}, 주제: {topic}")

#         # 각 플레이어에게 맞는 메시지를 개별 전송
#         for sid, player in players.items():
#             if player == liar:
#                 emit('liar_info', {'liar': True}, to=sid)  # 라이어에게 라이어임을 알림
#             else:
#                 emit('topic_info', {'topic': topic}, to=sid)  # 나머지에게 주제 전송

@socketio.on('start_game')
def start_game(room_id):
    players = rooms[room_id]['players']
    liar = random.choice(players)
    topic = "과일"  # 주제는 예시로 고정
    words = ["사과", "바나나", "포도", "귤", "딸기"]  # 예시 단어
    assignments = {player: random.choice(words) for player in players}
    assignments[liar] = "샤인머스켓"  # 라이어에게는 다른 단어 제공

    for player in players:
        emit('word_assigned', {'player': player, 'word': assignments[player]}, to=player)

    emit('game_started', room_id, broadcast=True)


@socketio.on('submit_sentence')
def submit_sentence(data):
    room_id = data['room_id']
    player_name = data['player_name']
    sentence = data['sentence']
    
    # 문장을 제출하고, 다른 플레이어에게 전송
    emit('sentence_submitted', {'player': player_name, 'sentence': sentence}, broadcast=True)

@socketio.on('guess_liar')
def guess_liar(data):
    room_id = data['room_id']
    guessed_liar = data['guessed_liar']
    player_name = data['player_name']
    
    if guessed_liar == rooms[room_id]['liar']:
        emit('result', f"{player_name}가 라이어를 맞췄습니다! 라이어는 {rooms[room_id]['liar']}입니다.", broadcast=True)
    else:
        emit('result', f"{player_name}가 틀렸습니다. 라이어는 {rooms[room_id]['liar']}입니다.", broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    # 플레이어가 연결을 끊을 때 목록에서 제거
    if request.sid in players:
        del players[request.sid]
        # 남아있는 플레이어들에게 업데이트된 목록을 전송
        emit('update_player_list', {'players': list(players.values())}, broadcast=True)

@socketio.on('new_game')
def new_game(room_id):
    # 방 상태 초기화
    rooms[room_id]['ready'] = []  # 준비 상태 초기화
    rooms[room_id]['started'] = False  # 게임 시작 상태 초기화
    emit('new_game_started', room_id, broadcast=True)  # 모든 플레이어에게 새로운 게임 시작 알림

if __name__ == '__main__':
    # eventlet을 사용하여 WebSocket 통신을 처리
    socketio.run(app, host='0.0.0.0', port=65432)
    # socketio.run(app, host='127.0.0.1', port=65432)
    
