from flask import Flask, render_template, request, jsonify
import json

app = Flask(__name__)

def load_questions():
    with open('test_questions.json') as f:
        questions = json.load(f)
    return questions

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/quiz')
def quiz():
    questions = load_questions()
    return jsonify(questions)

if __name__ == '__main__':
    app.run(debug=True)
