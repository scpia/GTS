from config import session, flash
import re
from flask_caching import Cache
import spotipy, random, json, logging

def get_spotify_client():
    token_info = session.get("token_info", None)
    if not token_info:
        return None
    sp = spotipy.Spotify(auth=token_info['access_token'])
    return sp

# Function to extract Playlist ID from Spotify Playlist URL
def extract_playlist_id(url):
    match = re.search(r'playlist/([a-zA-Z0-9]+)', url)
    if match:
        return match.group(1)
    return None

# Function to extract all Tracks from a given Playlist
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
            return json.jsonify({"success": False, "message": "Albums not found, please try again later."}), 404

        # If no albums found at all
        if not album_items:
            return json.jsonify({"success": False, "message": "No albums found for this artist."}), 404

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


def search_tracks(sp, query):
    results = sp.search(q=query, type='track', limit=30)
    tracks = results['tracks']['items']
    return [{'name': track['name'], 
             'artist': track['artists'][0]['name'], 
             'album_cover': track['album']['images'][0]['url']} for track in tracks]