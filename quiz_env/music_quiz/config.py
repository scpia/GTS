from flask import session, flash
from spotipy.oauth2 import SpotifyOAuth

# Spotify Auth Details
SPOTIPY_CLIENT_ID = "197fae76c16941eeb1004bb32363434d"
SPOTIPY_CLIENT_SECRET = "eed38db9ad374edb80efe73526291d9e"
SPOTIPY_REDIRECT_URI = "http://127.0.0.1:5000/callback"

# Initialize Spotify OAuth
sp_oauth = SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, scope="user-library-read user-top-read")

# You can add other shared configurations or functions here
