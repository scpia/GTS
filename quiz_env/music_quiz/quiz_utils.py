import json, requests

def fetch_questions(type_id,category_id,difficulty_id):
    url = f'https://opentdb.com/api.php?amount=10&type={type_id}&category={category_id}&difficulty={difficulty_id}'
    response = requests.get(url)  # Verwenden von requests.get() statt request.get()
    data = response.json()
    return data['results']

def load_questions():
    with open('test_questions.json') as f:
        questions = json.load(f)
    return questions