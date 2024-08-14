from flask import Flask, render_template, request, jsonify
import requests  # Verwenden der requests-Bibliothek für API-Anfragen
import json

app = Flask(__name__)

def fetch_questions(category_id):
    url = f'https://opentdb.com/api.php?amount=10&category={category_id}'
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

@app.route('/quiz-fragen/<int:category_id>')
def index(category_id):
    questions = fetch_questions(category_id)
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
if __name__ == '__main__':
    app.run(debug=True)
