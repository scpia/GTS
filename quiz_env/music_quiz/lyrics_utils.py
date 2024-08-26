from config import genius_init
from spotify_utils import get_spotify_client
import random



def filter_lyrics(lyrics):
    """
    Entfernt unerwünschte Platzhalter wie [Hook] aus den Lyrics und unterteilt sie in Verse.
    """
    import re
    # Regex-Muster für Platzhalter
    patterns = [r'\[.*?\]', r'\(.*?\)', r'\{.*?\}']
    
    for pattern in patterns:
        lyrics = re.sub(pattern, '', lyrics)

    # Lyrics in Zeilen unterteilen und Leerzeilen entfernen
    verses = lyrics.split("\n")
    filtered_verses = [verse.strip() for verse in verses if verse.strip() != ""]

    return filtered_verses


def fetch_lyrics_from_genius(sp, song_title, artist_name):
    """
    Ruft die Songtexte von Genius für einen bestimmten Song und Künstler ab.
    """
    # Song von Genius suchen
    song = genius_init.search_song(song_title, artist_name)
    if not song:
        raise ValueError(f"Text für den Song '{song_title}' konnte nicht abgerufen werden.")
    
    return song.lyrics

def fetch_random_song_from_spotify(sp, search_query):
    """
    Ruft einen zufälligen Song von Spotify basierend auf der Suchabfrage ab.
    """
    sp = get_spotify_client()
    results = sp.search(q=search_query, type='track', limit=50)
    tracks = results['tracks']['items']

    if not tracks:
        raise ValueError("Keine Songs gefunden.")

    # Zufälligen Song auswählen
    selected_track = random.choice(tracks)
    return selected_track