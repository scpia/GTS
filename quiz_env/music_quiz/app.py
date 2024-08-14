from flask import Flask, render_template, request, jsonify, redirect, session, url_for, flash
from spotipy.oauth2 import SpotifyOAuth
import json
import spotipy
import random

app = Flask(__name__)
#app.secret_key = "your_secret_key"  # Replace with your own secret key

# Spotify Auth Details
SPOTIPY_CLIENT_ID = "197fae76c16941eeb1004bb32363434d"  # Replace with your Spotify Client ID
SPOTIPY_CLIENT_SECRET = "eed38db9ad374edb80efe73526291d9e"  # Replace with your Spotify Client Secret
SPOTIPY_REDIRECT_URI = "http://localhost:5000/callback"

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


def get_spotify_client():
    token_info = session.get("token_info", None)
    if not token_info:
        return redirect(url_for('spotify_login'))
    sp = spotipy.Spotify(auth=token_info['access_token'])
    return sp


def get_random_track(sp):
    # Use a random search keyword or genre
    random_keywords = ['love', 'party', 'happy', 'rock', 'pop', 'jazz', 'chill', 'dance', 'summer']
    keyword = random.choice(random_keywords)

    results = sp.search(q=keyword, type='track', limit=50)
    tracks = results['tracks']['items']
    
    if not tracks:
        return None  # Handle case when no tracks are found

    return random.choice(tracks)


@app.route('/spotify-quiz', methods=['GET', 'POST'])
def spotify_quiz():
    sp = get_spotify_client()

    if request.method == 'GET':
        track = get_random_track(sp)

        if not track:
            flash("No tracks found! Please try again.", "danger")
            return redirect(url_for('spotify_quiz'))

        session['track_name'] = track['name'].lower()
        session['track_artist'] = track['artists'][0]['name'].lower()
        session['track_preview'] = track['preview_url']

        return render_template('spotify_quiz.html', preview_url=session['track_preview'])

    elif request.method == 'POST':
        user_song_name = request.form.get('song_name', '').strip().lower()
        user_artist_name = request.form.get('artist_name', '').strip().lower()

        correct_song_name = session.get('track_name')
        correct_artist_name = session.get('track_artist')

        if user_song_name == correct_song_name and user_artist_name == correct_artist_name:
            flash("Correct! Well done!", "success")
        else:
            flash(f"Wrong! The correct answer was '{correct_song_name}' by '{correct_artist_name}'", "danger")

        return redirect(url_for('spotify_quiz'))


if __name__ == '__main__':
    app.run(debug=True)
