from flask import Flask, render_template, request, jsonify, redirect, session, url_for, flash
from spotipy.oauth2 import SpotifyOAuth
import json
import spotipy
import random
import logging

logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
app.secret_key = "PaulIstEinHs"  # Replace with your own secret key

# Spotify Auth Details
SPOTIPY_CLIENT_ID = "197fae76c16941eeb1004bb32363434d"  # Replace with your Spotify Client ID
SPOTIPY_CLIENT_SECRET = "eed38db9ad374edb80efe73526291d9e"  # Replace with your Spotify Client Secret
SPOTIPY_REDIRECT_URI = "http://127.0.0.1:5000/callback"

sp_oauth = SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI,
                        scope="user-library-read user-top-read")

def load_questions():
    with open('test_questions.json') as f:
        questions = json.load(f)
    return questions

@app.route('/')
def menu():
    return render_template('menü.html')

@app.route('/quiz-fragen')
def index():
    return render_template('index.html')

@app.route('/quiz')
def quiz():
    questions = load_questions()
    return jsonify(questions)

# Spotify Authentication Route
@app.route('/spotify-login')
def spotify_login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    session.clear()  # Clear any existing session data
    code = request.args.get('code')
    if not code:
        flash("Authorization code not found.", "danger")
        return redirect(url_for('spotify_login'))

    token_info = sp_oauth.get_access_token(code)
    if not token_info:
        flash("Failed to retrieve access token.", "danger")
        return redirect(url_for('spotify_login'))

    session["token_info"] = token_info
    return redirect(url_for('spotify_quiz'))

@app.route('/test')
def test():
    return render_template('spotify_quiz.html', preview_url=None)

def get_spotify_client():
    token_info = session.get("token_info", None)
    if not token_info:
        # Redirect to Spotify login if token is not found
        return None
    sp = spotipy.Spotify(auth=token_info['access_token'])
    return sp

def get_random_track(sp):
    # Use a random search keyword or genre
    random_keywords = ['Kollegah']
    keyword = random.choice(random_keywords)

    results = sp.search(q=keyword, type='track', limit=50)
    tracks = results['tracks']['items']
    
    # Filter out tracks without a preview URL
    tracks_with_preview = [track for track in tracks if track['preview_url']]

    if not tracks_with_preview:
        return None  # Handle case when no tracks with a preview are found

    # Get Tracks that have been played already in current session
    played_tracks = session.get('played_tracks', [])

    tracks_to_choose_from = [track for track in tracks_with_preview if track['id'] not in played_tracks]

    if not tracks_to_choose_from:
        # If all tracks have been played, clear the session or reset it for the user
        session['played_tracks'] = []
        # You could also add logic here to fetch new tracks or retry with a different keyword
        return get_random_track(sp)  # Retry to get a fresh set of tracks

    # Select a random track that hasn't been played yet
    selected_track = random.choice(tracks_to_choose_from)
    
    # Update the session with the ID of the selected track
    played_tracks.append(selected_track['id'])
    session['played_tracks'] = played_tracks

    return selected_track

@app.route('/spotify-quiz', methods=['GET', 'POST'])
def spotify_quiz():
    sp = get_spotify_client()
    
    if sp is None:
        logging.debug("Spotify client is None, redirecting to login")
        return redirect(url_for('spotify_login'))

    if request.method == 'GET':
        try:
            track = get_random_track(sp)
            if not track:
                flash("No tracks found! Please try again.", "danger")
                return redirect(url_for('spotify_quiz'))

            session['track_name'] = track['name'].lower()
            session['track_artist'] = track['artists'][0]['name'].lower()
            session['track_preview'] = track['preview_url']
            return render_template('spotify_quiz.html', preview_url=session['track_preview'])
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            flash(f"An error occurred: {e}", "danger")
            return redirect(url_for('spotify_quiz'))

    elif request.method == 'POST':
        user_guess = request.form.get('song_guess', '').strip().lower()
        correct_song_name = session.get('track_name')
        correct_artist_name = session.get('track_artist')

        if correct_song_name in user_guess and correct_artist_name in user_guess:
            flash("Correct! Well done!", "success")
        else:
            flash(f"Wrong! The correct answer was '{correct_song_name}' by '{correct_artist_name}'", "danger")

        return redirect(url_for('spotify_quiz'))

# Neue Route für die Song-Suche mit Album-Cover
@app.route('/search')
def search():
    query = request.args.get('q')
    sp = get_spotify_client()
    
    if sp is None:
        return jsonify({'songs': []}), 401  # Nicht authentifiziert

    results = sp.search(q=query, type='track', limit=5)
    tracks = results['tracks']['items']
    songs = [{'name': track['name'], 
              'artist': track['artists'][0]['name'], 
              'album_cover': track['album']['images'][0]['url']} for track in tracks]

    return jsonify({'songs': songs})

if __name__ == '__main__':
    app.run(debug=True)
