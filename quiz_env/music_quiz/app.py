from flask import Flask, render_template, request, jsonify, redirect, session, url_for, flash
import requests  # Verwenden der requests-Bibliothek für API-Anfragen
from flask_caching import Cache
from spotipy.oauth2 import SpotifyOAuth
import json
import spotipy
import random
import logging
import re
import os

logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
cache = Cache(config={'CACHE_TYPE': 'simple'})
cache.init_app(app)
app.secret_key = "PaulIstEinHs"  # Replace with your own secret key
SCOREBOARD_FILE = 'scoreboard.json'



##################################################################
# Spotify Auth Details
SPOTIPY_CLIENT_ID = "197fae76c16941eeb1004bb32363434d"  # Replace with your Spotify Client ID
SPOTIPY_CLIENT_SECRET = "eed38db9ad374edb80efe73526291d9e"  # Replace with your Spotify Client Secret
SPOTIPY_REDIRECT_URI = "http://127.0.0.1:5000/callback"

sp_oauth = SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI,
                        scope="user-library-read user-top-read")

def fetch_questions(type_id,category_id,difficulty_id):
    url = f'https://opentdb.com/api.php?amount=10&type={type_id}&category={category_id}&difficulty={difficulty_id}'
    response = requests.get(url)  # Verwenden von requests.get() statt request.get()
    data = response.json()
    return data['results']

def load_questions():
    with open('test_questions.json') as f:
        questions = json.load(f)
    return questions

@app.route('/')
def menü():
    return render_template('menü.html')

@app.route('/quiz-fragen')
def quiz_fragen():
    # Lese die Filterparameter aus der Query-String
    category_id = request.args.get('category')
    difficulty = request.args.get('difficulty')
    question_type = request.args.get('type')
    print(question_type)
    # Erstelle die URL für die API-Abfrage
    url = "https://opentdb.com/api.php"
    params = {
        'amount': 10,  # Anzahl der Fragen (Beispielwert, kann angepasst werden)
        'category': category_id,
        'difficulty': difficulty,
        'type': question_type
    }

    # Entferne None-Werte aus den Parametern
    params = {key: value for key, value in params.items() if value is not None}

    try:
        # Hole die Fragen von der API
        response = requests.get(url, params=params)
        response.raise_for_status()  # Stelle sicher, dass die Anfrage erfolgreich war
        questions = response.json()['results']
        print(questions)
    except Exception as e:
        logging.error(f"Fehler beim Abrufen der Fragen: {e}")
        questions = []
    # Render die Template-Datei mit den Fragen
    return render_template('index.html', questions=questions)

@app.route('/fragen-themen')
def fragen_themen():
    return render_template('fragen-themen.html')

@app.route('/musik-fragen')
def musik_fragen():
    return render_template('musik-fragen.html')

@app.route('/quiz')
def quiz():
    category_id = request.args.get('category')
    if category_id:
        # API-Aufruf für Fragen basierend auf der Kategorie-ID
        url = f"https://opentdb.com/api.php?amount=10&category={category_id}"
        response = requests.get(url)  # Verwenden von requests.get() statt request.get()
        questions = response.json()
        return jsonify(questions)
    return jsonify({"error": "Category ID not provided"})

@app.route('/categories', methods=['GET'])
def get_categories():
    try:
        with open('quiz_env/music_quiz/categories.json', 'r') as file:
            categories = json.load(file)
        return jsonify(categories)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
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
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_info = sp.current_user()  # Get current user info
    session["spotify_id"] = user_info['id']  # Store Spotify ID in session
    session["display_name"] = user_info['display_name']  # Optionally store display name

    return redirect(url_for('choose'))


def get_spotify_client():
    token_info = session.get("token_info", None)
    if not token_info:
        return None
    sp = spotipy.Spotify(auth=token_info['access_token'])
    return sp

# Global Function to set Artist in Artist Mode
@app.route('/artist', methods=['GET', 'POST'])
def artist():
    if request.method == 'POST':
        data = request.get_json()
        artist_id = data.get('id')  # Get the artist_id from the POST data

        if artist_id:
            session['artist_id'] = artist_id

            sp = get_spotify_client()
            if not sp:
                return jsonify({"success": False, "message": "Spotify client not authenticated"}), 401

            # Fetch the artist's details directly using the artist_id
            artist_info = sp.artist(artist_id)
            artist_cover = artist_info['images'][0]['url'] if artist_info['images'] else 'default_image_url'
            session['artist_cover'] = artist_cover
            session['artist_name'] = artist_info['name']

            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "Artist ID not provided"}), 400
    return render_template('artist.html')  # Render a form or information page


# Select whether to play in Artist Mode or Playlist Mode
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


# Function to extract Playlist ID from Spotify Playlist URL
def extract_playlist_id(url):
    """
    Extracts the playlist ID from a Spotify playlist URL.
    """
    match = re.search(r'playlist/([a-zA-Z0-9]+)', url)
    if match:
        return match.group(1)
    return None

# Function to extract all Tracks from a given Playlist
@cache.memoize(timeout=3600)  # Cache for 1 hour
def get_all_tracks_from_playlist(sp, playlist_id):
    tracks = []
    results = sp.playlist_tracks(playlist_id)
    filtered_tracks = [track for track in results['items'] if 'instrumental' not in track['track']['name'].lower()]
    tracks.extend(filtered_tracks)

    while results['next']:
        results = sp.next(results)
        filtered_tracks = [track for track in results['items'] if 'instrumental' not in track['track']['name'].lower()]
        tracks.extend(filtered_tracks)

    return tracks

def initialize_track_list(sp):
    artist_id = session.get('artist_id')  # Use artist_id from the session
    playlist_link = session.get('playlist_link')
    
    if artist_id:
        # Fetch albums directly using the artist ID
        albums = sp.artist_albums(artist_id, album_type='album,single')
        album_items = albums['items']
        album_ids = [album['id'] for album in album_items]

        # Check if the items array is empty despite a non-zero total
        if not album_items and albums['total'] > 0:
            # Log the issue
            logging.warning(f"Expected {albums['total']} albums but received none for artist {artist_id}")
            return jsonify({"success": False, "message": "Albums not found, please try again later."}), 404

        # If no albums found at all
        if not album_items:
            return jsonify({"success": False, "message": "No albums found for this artist."}), 404

        # Store album_ids or a reference instead of full tracks
        session['album_ids'] = album_ids
        session.modified = True

    elif playlist_link:
        playlist_id = extract_playlist_id(playlist_link)

        if not playlist_id:
            flash("Invalid playlist URL.", "danger")
            return None
        
        # Store playlist_id instead of full tracks
        session['playlist_id'] = playlist_id
        session.modified = True

    else:
        # Handle other cases
        session['search_keyword'] = 'Farid Bang'
        session.modified = True



# Extract Tracks from initialisze_track_list
def get_tracks_from_session(sp):
    album_ids = session.get('album_ids')
    playlist_id = session.get('playlist_id')
    keyword = session.get('search_keyword')
    is_Playlist = False

    if album_ids:
        # Fetch tracks based on album_ids
        tracks = []
        chosen_album = random.choice(album_ids)
        album_tracks = sp.album_tracks(chosen_album)
        filtered_tracks = [track for track in album_tracks['items'] if 'instrumental' not in track['name'].lower()]
        tracks.extend(filtered_tracks)
        return tracks, is_Playlist

    elif playlist_id:
        # Fetch tracks based on playlist_id
        tracks = get_all_tracks_from_playlist(sp, playlist_id)
        is_Playlist = True
        return tracks, is_Playlist

    elif keyword:
        # Fetch tracks based on search keyword
        tracks = search_tracks(sp, keyword)
        return tracks, is_Playlist

    return [], is_Playlist

# Select a random Track from the track list in the session
def get_random_track(sp):
    tracks, is_Playlist = get_tracks_from_session(sp)
    if not tracks:
        flash("Track list is empty or not initialized. Please restart the quiz.", "danger")
        return None, None

    track = random.choice(tracks)
    return track, is_Playlist

@cache.memoize(timeout=600)  # Cache search results for 10 minutes
def search_tracks(sp, query):
    results = sp.search(q=query, type='track', limit=30)
    tracks = results['tracks']['items']
    return [{'name': track['name'], 
             'artist': track['artists'][0]['name'], 
             'album_cover': track['album']['images'][0]['url']} for track in tracks]

# Function to display Suggestion in Guessing State --> Song Guess
@app.route('/search')
def search():
    query = request.args.get('q')
    sp = get_spotify_client()
    
    # Check if API Connection is established
    if sp is None:
        return jsonify({'songs': []}), 401  # Not authenticated

    try:
        songs = search_tracks(sp, query)
        return jsonify({'songs': songs})
    except Exception as e:
        logging.error(f"Search failed: {e}")
        return jsonify({'songs': []}), 500  # Internal Server Error

# Function to display Suggestion in Artist Query
@cache.memoize(timeout=600)  # Cache search results for 10 minutes
@app.route('/search_artist')
def search_artist():
    query = request.args.get('q')
    sp = get_spotify_client()
    
    # Check if API Connection is established
    if sp is None:
        return jsonify({'artists': []}), 401  # Not authenticated

    try:
        # Perform search for artists based on the query
        results = sp.search(q=f'artist:{query}', type='artist', limit=10)
        artists = results['artists']['items']
        
        # Use a dictionary to avoid duplicates
        unique_artists = {artist['name']: artist for artist in artists}
        
        # Create a list of artist suggestions including their name and image
        artist_suggestions = [
            {
                'artist': artist['name'],
                'id': artist['id'],
                'image': artist['images'][0]['url'] if artist['images'] else 'default_image_url'
                
            } for artist in unique_artists.values()
        ]
        
        return jsonify({'artists': artist_suggestions})
    except Exception as e:
        logging.error(f"Artist search failed: {e}")
        return jsonify({'artists': []}), 500  # Internal Server Error


def load_scoreboard():
    if not os.path.exists(SCOREBOARD_FILE):
        # If the file doesn't exist, create an empty scoreboard
        with open(SCOREBOARD_FILE, 'w') as f:
            json.dump({}, f)  # Create an empty JSON object

    # Load the scoreboard from the file
    with open(SCOREBOARD_FILE, 'r') as f:
        scoreboard = json.load(f)

    # Convert old structure to new structure if necessary
    for user_id, value in scoreboard.items():
        if isinstance(value, int):  # Old structure
            scoreboard[user_id] = {"current_score": 0, "high_score": value}

    return scoreboard

def save_scoreboard(scoreboard):
    try:
        with open(SCOREBOARD_FILE, 'w') as f:
            json.dump(scoreboard, f, indent=4)
            print(f"Scoreboard saved successfully: {scoreboard}")
    except Exception as e:
        print(f"Error saving scoreboard: {e}")

def reset_current_score(user_id):
    scoreboard = load_scoreboard()
    
    if user_id in scoreboard:
        scoreboard[user_id]['current_score'] = 0
    else:
        scoreboard[user_id] = {'current_score': 0, 'high_score': 0}
    
    save_scoreboard(scoreboard)


def update_score(user_id, score):
    scoreboard = load_scoreboard()
    
    # Ensure we have a valid entry for the user
    user_scores = scoreboard.get(user_id, {'current_score': 0, 'high_score': 0})
    
    # If the existing entry is just an integer (legacy), convert it to the new format
    if isinstance(user_scores, int):
        user_scores = {'current_score': 0, 'high_score': user_scores}
    
    # Update the current score
    user_scores['current_score'] += score
    
    # Update the high score if the current score exceeds it
    if user_scores['current_score'] > user_scores['high_score']:
        user_scores['high_score'] = user_scores['current_score']
    
    # Save the updated scores back to the scoreboard
    scoreboard[user_id] = user_scores
    save_scoreboard(scoreboard)

    # Log the updated scores for debugging
    logging.debug(f"Updated scores for user {user_id}: {user_scores}")





@app.route('/scoreboard')
def scoreboard():
    scoreboard = load_scoreboard()
    # Sort the scoreboard by score in descending order
    sorted_scoreboard = sorted(scoreboard.items(), key=lambda x: x[1], reverse=True)
    return render_template('scoreboard.html', scoreboard=sorted_scoreboard)


@app.route('/spotify-quiz', methods=['GET', 'POST'])
def spotify_quiz():
    sp = get_spotify_client()
    
    if sp is None:
        logging.debug("Spotify client is None, redirecting to login")
        return redirect(url_for('spotify_login'))

    user_id = session.get('spotify_id')
    scoreboard = load_scoreboard()
    
    user_scores = scoreboard.get(user_id, {})
    if isinstance(user_scores, int):  # Handle old structure
        user_scores = {"current_score": 0, "high_score": user_scores}
    
    current_score = user_scores.get('current_score', 0)
    high_score = user_scores.get('high_score', 0)
    
    if request.method == 'GET':
        initialize_track_list(sp)
        if not session.get('album_ids') and session.get('playlist_id'):
            reset_current_score(user_id)  # Reset current score for new game

        track, is_Playlist = get_random_track(sp)

        if track is None:
            return redirect(url_for('spotify_quiz'))  # Or return an error page

        # Handle case when playing with a Playlist or Artist
        if is_Playlist:
            session['track_name'] = track['track']['name'].lower()
            session['track_artist'] = track['track']['artists'][0]['name'].lower()
            session['track_preview'] = track['track']['preview_url']
        else:
            session['track_name'] = track['name'].lower()
            session['track_artist'] = track['artists'][0]['name'].lower()
            session['track_preview'] = track['preview_url']

        return render_template('spotify_quiz.html', 
                               preview_url=session['track_preview'],
                               current_score=current_score,
                               high_score=high_score,
                               artist_cover=session.get('artist_cover'),
                               artist_name=session.get('artist_name'))

    elif request.method == 'POST':
        user_guess = request.form.get('song_guess', '').strip().lower()
        correct_song_name = session.get('track_name')
        correct_artist_name = session.get('track_artist')
        spotify_id = session.get('spotify_id')

        if correct_song_name in user_guess and correct_artist_name in user_guess:
            flash("Correct! Well done!", "success")
            update_score(spotify_id, 1)  # Update the score for the user
        else:
            flash(f"Wrong! The correct answer was '{correct_song_name}' by '{correct_artist_name}'", "danger")

        track, is_Playlist = get_random_track(sp)
        if track is None:
            flash("No more tracks available! Please refresh the quiz.", "info")
            return redirect(url_for('spotify_quiz'))  # Or handle as needed

        return redirect(url_for('spotify_quiz'))






if __name__ == '__main__':
    app.run(debug=True)