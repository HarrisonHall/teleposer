"""
application.py
==============

"""

from flask import Flask, render_template, request, jsonify
from flask import flash, redirect, session, url_for
from flask_socketio import SocketIO, join_room, leave_room
from flask_socketio import emit, rooms
from json import dumps
from src import ti


app = Flask(__name__, template_folder="./templates", static_folder="./static")
app.secret_key = b"imposter_telephone_secret_key"
socketio = SocketIO(app, logger=True)

@app.route("/")
def index():
    return render_template(
        "pages/index.html",
        context={}
    )

@app.route("/ti_game", methods=["POST"])
def create_join_request():
    if not ti.is_error(ti.create_or_join(
            session, request.form["username"], request.form["room_code"])
    ):
        # Set session
        session["username"] = request.form["username"]
        session["room_code"] = request.form["room_code"]
        # Remove from rooms
        """ TODO
        for room in rooms():
            leave_room(room)
        """
        return render_template(
            "pages/telephone_imposter.html",
            context={
                "game_data": dumps(ti.get_game(request.form["room_code"])),
                "room_code": request.form["room_code"],
            }
        )
    else:
        flash("Unable to connect to room")
        return redirect(url_for("index"))

@socketio.on("ti_connected")
def handle_ti_connection(data):
    # Leave old rooms
    for room in rooms():
        leave_room(room)
    # Join new room
    join_room(session["room_code"])
    # Update users
    emit("ti_update", ti.game_context(session, session["room_code"]), room=session["room_code"])

@socketio.on("ti_update_settings")
def handle_ti_settings_update(data):
    # Update settings
    ti.games[session["room_code"]]["settings"]["words"] = int(data["words"])
    ti.games[session["room_code"]]["settings"]["mixup"] = int(data["mixup"])
    if len(ti.games[session["room_code"]]["players"]) >= 2: # TODO 4
        ti.games[session["room_code"]]["state"] = ti.PLAYING
        ti.determine_imposter(session["room_code"])
    # Emit updates/Start game
    emit("ti_update", ti.game_context(session, session["room_code"]), room=session["room_code"])

@socketio.on("ti_submit_sentence")
def handle_ti_submit_sentence(data):
    print(data["sentence"])
    sentence = ti.filter_sentence(data["sentence"])
    print(sentence)
    user_submitted_for = data["user"]
    words = sentence.split(" ")
    print(words)
    if user_submitted_for == session["username"]:
        if ti.games[session["room_code"]]["phrases"].get(session["username"], []):
            return # User submitting twice error
    if len(words) < ti.games[session["room_code"]]["settings"]["words"]:
        flash("Not enough words")
        return
    if len(words) > ti.games[session["room_code"]]["settings"]["words"]:
        flash("Too many words")
        return
    if ti.submit_words(session["room_code"], session["username"], sentence, user_submitted_for):
        ti.mixup_words(user_submitted_for, session["room_code"])
        ti.calculate_phase(session["room_code"])
        emit("ti_update", ti.game_context(session, session["room_code"]), room=session["room_code"])
        return
    else:
        # TODO error
        flash("ERROR")
        return

@socketio.on("ti_vote")
def handle_ti_vote(vote):
    user = vote["user"]
    vote_for = vote["vote"]
    ti.games[session["room_code"]]["votes"][user] = vote_for
    ti.calculate_phase(session["room_code"])
    emit("ti_update", ti.game_context(session, session["room_code"]), room=session["room_code"])
    # Handle game over
    if ti.games[session["room_code"]]["state"] == ti.OVER:
        del ti.games[session["room_code"]]
    
if __name__ == '__main__':
    socketio.run(app, debug=True)
