from flask import Flask, request, url_for, session, redirect, render_template
from flask_socketio import join_room, leave_room, send, SocketIO, emit
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import random
from string import ascii_uppercase
from flask_session import Session
import os

# Notes
# You can pass variables into the html code like below:
# using render_template("example.html", variable_name=...)
#
# You can get the form to perform a method
# <form method="methodName">

# Make a check for every member to include in the comparison

# If it doesn't work outright (please god i beg you pls work)
# Send message to server when a new person connects
# Room page refreshes
# then run compare()
# pass back the resulting list

# what if i need /room/code
# maybe there's only room for 1 room & since leaving the room doesn't delete the stuff that was in there, it doesn't show new users' stuff
# in which case, updating the room page is also broken (either it can't tell when a new person has joined or it just doesn't update right)

# It could be spotify's API (i give my client secret & client id)

# ok it's just not updating correctly
# new people can't see previous results

# initialize
app = Flask(__name__)
os.environ["SPOTIPY_CLIENT_ID"] = "77771486cf5e471fb94e32197e9035e9"
os.environ["SPOTIPY_CLIENT_SECRET"] = "0009c35f5bd248e1a4234a1f2a765b1c"
os.environ["SPOTIPY_REDIRECT_URI"] = 'https://neccpain.pythonanywhere.com/'
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)
socketio = SocketIO(app)
rooms = {}

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)

        if code not in rooms:
            break

    return code

@app.route('/',  methods=["POST", "GET"])
@app.route('/index',  methods=["POST", "GET"])
def index():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope='user-top-read',
                                               cache_handler=cache_handler,
                                               show_dialog=True)
           
    if request.method == "POST":
        sp = spotipy.Spotify(auth_manager=auth_manager)
        join_code = request.form.get("join_code")
        join_btn = request.form.get("join_btn", False)
        create = request.form.get("create", False)

        if join_btn != False and not join_code:
            return render_template('index.html', error="Please enter a room code")

        room = join_code
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "content" : []}
        elif join_code not in rooms:
            return render_template('index.html', error="Room does not exist", join_code=join_code)

        session["room"] = room
        session["name"] = sp.me()["display_name"]

        return redirect(url_for("room"))

    if request.args.get("code"):
        # Step 2. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return render_template('index.html', flag=1)

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 1. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return render_template('index.html', auth_url=auth_url, flag=0)

    # Step 3. Signed in, display data
           
    return render_template('index.html')
    
@app.route('/room')
def room():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    auth_url = auth_manager.get_authorize_url()

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect(url_for('index.html', auth_url=auth_url, flag=0))
    
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for('index.html', flag=1))
    
    sp = spotipy.Spotify(auth_manager=auth_manager)

    items = []
    for i in range(0, 5):
        for item in sp.current_user_top_tracks(limit=50, offset=i*50)['items']:
            # appends the album cover, track title, artist, and song id
            items += [item['album']['images'][2]['url'], item['name'], item['artists'][0]['name'], item['id']]

    session["items"] = items

    if {"user":session.get("name"), "tracks":items} not in rooms[room]["content"]:
        # appends user's tracks into the room's content if they're not already in there
        rooms[room]["content"].append({"user":session.get("name"), "tracks":items})

    return render_template('room.html', code=room, content=rooms[room]["content"])

@socketio.on("connect")
def on_connect(auth):
    room = session.get("room")
    name = session.get("name")
    items = session.get("items")

    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return

    join_room(room)
    data = {"name": name, "items": items}
    send(data, to=room)
    rooms[room]["members"] += 1

@socketio.on("requestSongs")
def requestSongs(user):
    room = session.get("room")
    if room not in rooms:
        return
    
    for data in rooms[room]["content"]:
        if user == data["user"]:
            emit("sendSongs", (user, data["tracks"]), to=room)

@socketio.on("requestClear")
def requestClear(user):
    room = session.get("room")
    if room not in rooms:
        return
    
    for data in rooms[room]["content"]:
        if user == data["user"]:
            emit("sendClear", user, to=room)


@socketio.on("disconnect")
def on_disconnect():
    room = session.get("room")
    leave_room(room)
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]

if __name__ == '__main__':
    socketio.run(app, debug=True)
