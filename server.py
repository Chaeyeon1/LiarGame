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

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join_game')
def handle_join_game(player_name):
    global liar, topic, hints_submitted, guesses_submitted

    # 새로운 플레이어를 플레이어 목록에 추가하고 소켓 ID 저장
    players[request.sid] = player_name

    # 모든 플레이어들에게 현재 방에 있는 플레이어 목록을 전송
    emit('update_player_list', {'players': list(players.values())}, broadcast=True)

    # 플레이어가 다 모이면 라이어와 주제를 설정
    if len(players) == total_players:
        liar = random.choice(list(players.values()))
        topic = random.choice(topics)
        hints_submitted = 0  # 힌트 제출 수 초기화
        guesses_submitted = 0  # 추측 제출 수 초기화

        print(f"라이어: {liar}, 주제: {topic}")

        # 각 플레이어에게 맞는 메시지를 개별 전송
        for sid, player in players.items():
            if player == liar:
                emit('liar_info', {'liar': True}, to=sid)  # 라이어에게 라이어임을 알림
            else:
                emit('topic_info', {'topic': topic}, to=sid)  # 나머지에게 주제 전송

@socketio.on('submit_hint')
def handle_hint(data):
    global hints_submitted

    player = players[request.sid]
    hint = data['hint']
    hints_submitted += 1
    send(f"{player}의 힌트: {hint}", broadcast=True)

    # 모든 플레이어가 힌트를 제출하면 추측 단계로 이동
    if hints_submitted == total_players:
        send("모든 힌트가 제출되었습니다. 이제 라이어를 추측하세요!", broadcast=True)
        emit('start_guessing', broadcast=True)  # 클라이언트에 추측 시작을 알림

@socketio.on('guess_liar')
def handle_guess(data):
    global guesses_submitted

    guess = data['guess']
    player = players[request.sid]
    guesses_submitted += 1

    if guess == liar:
        send(f"{player}가 맞췄습니다! 라이어는 {liar}입니다.", broadcast=True)
    else:
        send(f"{player}가 틀렸습니다. 라이어는 {liar}입니다.", broadcast=True)

    # 모든 플레이어가 추측을 끝냈으면 게임 종료 메시지 출력
    if guesses_submitted == total_players:
        send("게임이 종료되었습니다. 모두 고생하셨습니다!", broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    # 플레이어가 연결을 끊을 때 목록에서 제거
    if request.sid in players:
        del players[request.sid]
        # 남아있는 플레이어들에게 업데이트된 목록을 전송
        emit('update_player_list', {'players': list(players.values())}, broadcast=True)

if __name__ == '__main__':
    # eventlet을 사용하여 WebSocket 통신을 처리
    socketio.run(app, host='0.0.0.0', port=65432)
    # socketio.run(app, host='127.0.0.1', port=65432)
