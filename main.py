from flask import Flask, request, url_for, session, redirect, render_template
from flask_socketio import join_room, leave_room, send, SocketIO
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import random
from string import ascii_uppercase

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


# initialize
app = Flask(__name__)
app.secret_key = "038nsu3sYn82y"
app.config['SESSION_COOKIE_NAME'] = "Test Cookie"
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

@app.route('/')
@app.route('/index')
def index():
    session.clear()
    return render_template('index.html')

@app.route("/connect")
def connect():
    #Logs you into spotify
    #Home page for now, but change later
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/create')
def create():
    pass

@app.route('/join')
def join():
    pass

@app.route('/authorize')
def authorize():
    #After the user logqs in, they get redirected here
    sp_oauth = create_spotify_oauth()
    session.clear()

    #flask requires this request object
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info #saves the token info in the session

    return redirect(url_for('menu', _external=True))

@app.route('/menu', methods=["POST", "GET"])
def menu():
    if request.method == "POST":
        join_code = request.form.get("join_code")
        join_btn = request.form.get("join_btn", False)
        create = request.form.get("create", False) #returns False when they're pressed

        if join_btn != False and not join_code:
            return render_template('menu.html', error="Please enter a room code")
        
        room = join_code
        if create != False:
            room = generate_unique_code(4)
            print(f"code: {room}")
            rooms[room] = {"members": 0, "tracks": []}
        elif join_code not in rooms:
            return render_template('menu.html', error="Room does not exist", join_code=join_code)

        try:
            token_info = get_token()
        except:
            print("User not logged in")
            return redirect(url_for("login", _external=True))
        sp = spotipy.Spotify(auth=token_info["access_token"])

        session["room"] = room #semi-permanent way to store data
        session["name"] = sp.me()["display_name"]

        return redirect(url_for("room"))

    return render_template('menu.html')

@app.route('/room')
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("menu"))
    
    try:
        token_info = get_token()
    except:
        print("User not logged in")
        return redirect(url_for("login", _external=True))
    
    sp = spotipy.Spotify(auth=token_info["access_token"])

    #to be done later
    items = []
    for i in range(0, 3):
        for item in sp.current_user_top_tracks(limit=50, offset=i)['items']:
            # items += {"Artist": item['artists'][0]['name'], "Title": item['name'], "Cover": item['album']['images'][1]['url']}
            items += [item['album']['images'][2]['url'], item['name'], item['artists'][0]['name']]

    session["items"] = items

    return render_template('room.html', code=room, members=rooms[room]["members"])

@app.route('/test')
def test():
    try:
        token_info = get_token()
    except:
        print("User not logged in")
        return redirect(url_for("login", _external=True))
    
    sp = spotipy.Spotify(auth=token_info["access_token"])

    return sp.current_user_top_tracks(limit=50, offset=0)['items']



def create_spotify_oauth():
    #Creates a SpotifyOAuth object
    return SpotifyOAuth(
        client_id = "77771486cf5e471fb94e32197e9035e9",
        client_secret = "0009c35f5bd248e1a4234a1f2a765b1c",
        redirect_uri = url_for("authorize", _external=True),
        scope = "user-top-read"
    )

def get_token():
    #Checks if access token is expired & gets a new one if it is
    #Also checks if there IS token data, if not redirect to login
    token_info = session.get("token_info", {})

    if not token_info:
        raise "Exception"
    
    now = int(time.time())
    is_expired = token_info["expires_at"] - now < 60
    if is_expired:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info["refresh_token"])

    return token_info

def compare():

    pass

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    items = session.get("items")

    if not room and not name:
        return 
    if room not in rooms:
        leave_room(room)
        return 
    
    join_room(room)

    data = {"name": name, "items":items}
    send(data, to=room)

    rooms[room]["members"] += 1

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]


#start
if __name__ == '__main__':  
    app.run()
