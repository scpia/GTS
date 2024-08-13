from flask import Flask, render_template, request, jsonify
import json

app = Flask(__name__)

def load_questions():
    with open('test_questions.json') as f:
        questions = json.load(f)
    return questions


@app.route('/')
def menü():
    return render_template('menü.html')


@app.route('/quiz-fragen')
def index():
    return render_template('index.html')


@app.route('/musik-fragen')
def musik_fragen():
    return render_template('musik-fragen.html')

@app.route('/quiz')
def quiz():
    questions = load_questions()
    return jsonify(questions)

if __name__ == '__main__':
    app.run(debug=True)
