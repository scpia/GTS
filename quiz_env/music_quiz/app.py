from flask import Flask, render_template, request, jsonify, redirect, session, url_for, flash
from flask_caching import Cache
from config import sp_oauth, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, SpotifyOAuth
from spotify_utils import get_random_track, get_spotify_client, search_tracks, initialize_track_list, Cache
from scoreboard_utils import reset_current_score, load_scoreboard, update_score, save_scoreboard
import json, spotipy, logging, re, requests


logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
cache.init_app(app)
app.secret_key = "PaulIstEinHs"  # Replace with your own secret key

##################################################################
# Spotify Auth Details
sp_oauth = SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI,
                        scope="user-library-read user-top-read")

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

# Select whether you want to play with artist or playlist
@app.route('/choose', methods=['GET', 'POST'])
def choose():
    sp = get_spotify_client()
    if request.method == 'POST':
        choice = request.form.get('choice')
        
        if choice == 'artist':
            return redirect(url_for('artist'))
        
        elif choice == 'playlist':
            playlist_link = request.form.get('playlist_link')
            if not playlist_link:  # Validate the playlist link
                flash("Please provide a valid playlist link.", "error")
                return redirect(url_for('choose'))

            # Extract the playlist ID using regex
            playlist_id_match = re.search(r'playlist/([a-zA-Z0-9]+)', playlist_link)
            if playlist_id_match:
                playlist_id = playlist_id_match.group(1)
            else:
                flash("Invalid Spotify playlist link.", "error")
                return redirect(url_for('choose'))
            
            try:
                # Fetch the playlist cover image using the playlist ID
                cover_image = sp.playlist_cover_image(playlist_id)
                session['artist_cover'] = cover_image[0]['url']  # Assuming the first image is the one you need
                session['playlist_link'] = playlist_link
                return redirect(url_for('spotify_quiz'))
            except Exception as e:
                flash(f"An error occurred: {str(e)}", "error")
                return redirect(url_for('choose'))
    
    return render_template('choose.html')


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
@app.route('/search_artist')
@cache.cached(timeout=60)
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
        
        # Use a dictionary to track unique artist names and IDs
        unique_artists = {}
        artist_suggestions = []

        for artist in artists:
            artist_name = artist['name'].lower()  # Normalize the name to lower case for consistency
            artist_id = artist['id']

            # Create a unique key based on artist name and ID to avoid duplicates
            unique_key = f"{artist_name}"
            
            if unique_key not in unique_artists:
                unique_artists[unique_key] = True  # Mark this artist as seen
                
                # Handle the artist image (use a default image if not available)
                artist_image = artist['images'][0]['url'] if artist['images'] else url_for('static', filename='default_image.png')
                
                artist_suggestions.append({
                    'artist': artist['name'],  # Use the original name (not lowercased)
                    'id': artist_id,
                    'image': artist_image
                })

        return jsonify({'artists': artist_suggestions})
    except Exception as e:
        logging.error(f"Artist search failed: {e}")
        return jsonify({'artists': []}), 500  # Internal Server Error


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