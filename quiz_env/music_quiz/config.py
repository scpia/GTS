from spotipy.oauth2 import SpotifyOAuth
import lyricsgenius

# Spotify Auth Details
SPOTIPY_CLIENT_ID = "197fae76c16941eeb1004bb32363434d"
SPOTIPY_CLIENT_SECRET = "eed38db9ad374edb80efe73526291d9e"
SPOTIPY_REDIRECT_URI = "http://127.0.0.1:5000/callback"

# Initialize Spotify OAuth
sp_oauth = SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, scope="user-library-read user-top-read")

# Initialize Genius API
GENIUS_API_TOKEN = "XKguZrxNgVgiJKbq096Dum4gRW1zbmuMfKRAIVPVTrqMGWf29IXAmypSbcsm3hGJ"
genius_init = lyricsgenius.Genius(GENIUS_API_TOKEN)