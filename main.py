from flask import Flask, request, url_for, session, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time

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
    sp_oauth = create_spotify_oauth()
    session.clear()

    #flask requires this request object
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info #saves the token info in the session

    return redirect(url_for('getTracks', _external=True))

@app.route('/getTracks')
def getTracks():
    try:
        token_info = get_token()
    except:
        print("User not logged in")
        return redirect(url_for("login", _external=True))
    sp = spotipy.Spotify(auth=token_info["access_token"])
    return sp.current_user_top_artists(limit=50, offset=0)['items']

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
        raise "Execption"
    
    now = int(time.time())
    is_expired = token_info["expires_at"] - now < 60
    if is_expired:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info["refresh_token"])
    return token_info

#start
if __name__ == '__main__':  
    app.run()
