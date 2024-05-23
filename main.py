from flask import Flask, request, url_for, session, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)

app.secret_key = "038nsu3sYn82y"
app.config['SESSION_COOKIE_NAME'] = "Test Cookie"

@app.route('/')
def login():
    #Logs you into spotify
    #Home page for now, but change later
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/authorize')
def authorize():
    #After the user logs in, they get redirected here
    return "authorized"

@app.route('/getTracks')
def getTracks():
    #placeholder
    return "Tracks"

def create_spotify_oauth():
    #Creates a SpotifyOAuth object
    return SpotifyOAuth(
        client_id = "77771486cf5e471fb94e32197e9035e9",
        client_secret = "0009c35f5bd248e1a4234a1f2a765b1c",
        redirect_uri = url_for("authorize", _external=True),
        scope = "user-library-read"
    )

#start
if __name__ == '__main__':  
    app.run()
