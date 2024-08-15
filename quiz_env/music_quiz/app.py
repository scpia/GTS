from flask import Flask, render_template, request, jsonify, redirect, session, url_for, flash
from flask_caching import Cache
from spotipy.oauth2 import SpotifyOAuth
import json
import spotipy
import random
import logging
import re

logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
cache = Cache(config={'CACHE_TYPE': 'simple'})
cache.init_app(app)
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
    session.clear()
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
    return redirect(url_for('choose'))

@app.route('/choose', methods=['GET', 'POST'])
def choose():
    if request.method == 'POST':
        choice = request.form.get('choice')
        if choice == 'artist':
            return redirect(url_for('artist'))
        elif choice == 'playlist':
            playlist_link = request.form.get('playlist_link')
            session['playlist_link'] = playlist_link
            return redirect(url_for('spotify_quiz'))
    
    return render_template('choose.html')

@app.route('/artist', methods=['GET', 'POST'])
def artist():
    if request.method == 'POST':
        artist_name = request.form.get('artist_name')
        flash(f"Artist '{artist_name}' submitted successfully!", "success")
        session['artist'] = artist_name
        return redirect(url_for('spotify_quiz'))
    return render_template('artist.html')

@app.route('/test')
def test():
    return render_template('spotify_quiz.html', preview_url=None)

def get_spotify_client():
    token_info = session.get("token_info", None)
    if not token_info:
        return None
    sp = spotipy.Spotify(auth=token_info['access_token'])
    return sp

def extract_playlist_id(url):
    """
    Extracts the playlist ID from a Spotify playlist URL.
    """
    match = re.search(r'playlist/([a-zA-Z0-9]+)', url)
    if match:
        return match.group(1)
    return None

@cache.memoize(timeout=3600)  # Cache for 1 hour
def get_all_tracks_from_playlist(sp, playlist_id):
    tracks = []
    results = sp.playlist_tracks(playlist_id)
    tracks.extend(results['items'])

    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    return tracks

@cache.memoize(timeout=600)  # Cache search results for 10 minutes
def search_tracks(sp, query):
    results = sp.search(q=query, type='track', limit=10)
    tracks = results['tracks']['items']
    return [{'name': track['name'], 
             'artist': track['artists'][0]['name'], 
             'album_cover': track['album']['images'][0]['url']} for track in tracks]

def get_random_track(sp):
    artist_name = session.get('artist')
    playlist_link = session.get('playlist_link')
    
    if artist_name:
        results = sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
        artist = results['artists']['items']

        if not artist:
            flash(f"No artist found with name '{artist_name}'", "danger")
            return redirect(url_for('choose'))
        
        artist_id = artist[0]['id']
        albums = sp.artist_albums(artist_id, album_type='album', limit=50)
        album_ids = [album['id'] for album in albums['items']]

        tracks = []
        for album_id in album_ids:
            album_tracks = sp.album_tracks(album_id)
            tracks.extend(album_tracks['items'])

    elif playlist_link:
        playlist_id = extract_playlist_id(playlist_link)
        if not playlist_id:
            flash("Invalid playlist URL.", "danger")
            return redirect(url_for('choose'))

        tracks = get_all_tracks_from_playlist(sp, playlist_id)

    else:
        random_keywords = ['Farid Bang']
        keyword = random.choice(random_keywords)
        tracks = search_tracks(sp, keyword)

    tracks_with_preview = [track for track in tracks if track['preview_url']]

    if not tracks_with_preview:
        return None

    played_tracks = session.get('played_tracks', [])

    tracks_to_choose_from = [track for track in tracks_with_preview if track['id'] not in played_tracks]

    if not tracks_to_choose_from:
        session['played_tracks'] = []
        return get_random_track(sp)  # Retry to get a fresh set of tracks

    selected_track = random.choice(tracks_to_choose_from)
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

@app.route('/search')
def search():
    query = request.args.get('q')
    sp = get_spotify_client()
    
    if sp is None:
        return jsonify({'songs': []}), 401  # Not authenticated

    try:
        songs = search_tracks(sp, query)
        return jsonify({'songs': songs})
    except Exception as e:
        logging.error(f"Search failed: {e}")
        return jsonify({'songs': []}), 500  # Internal Server Error

if __name__ == '__main__':
    app.run(debug=True)
