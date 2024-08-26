import os
import json
import logging

SCOREBOARD_FILE = 'scoreboard.json'

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