fetch('/quiz')
/*     .then(response => response.json())
    
    .then(data => {
        console.log(data);
        const container = document.getElementById('quiz-container');
        data.forEach((question, index) => {
            const questionElement = document.createElement('div');
            questionElement.innerHTML = `<p>${index + 1}. ${question.question}</p>`;
            question.options.forEach(option => {
                questionElement.innerHTML += `<input type="radio" name="q${index}" value="${option}"> ${option}<br>`;
            });
            container.appendChild(questionElement);
        });
    }); */

    const apiUrl = "https://opentdb.com/api.php?amount=10"

    fetch(apiUrl)
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();  // Die Antwort als JSON parsen
    })
    .then(data => {
        const container = document.getElementById('quiz-container');
        if (!container) {
            console.error('Quiz container not found!');
            return;
        }

        data.results.forEach((question, index) => {
            const questionElement = document.createElement('div');
            questionElement.innerHTML = `<p>${index + 1}. ${question.question}</p>`;
            
            question.incorrect_answers.forEach(option => {
                questionElement.innerHTML += `<input type="radio" name="q${index}" value="${option}"> ${option}<br>`;
            });
            
            questionElement.innerHTML += `<input type="radio" name="q${index}" value="${question.correct_answer}"> ${question.correct_answer}<br>`;
            
            container.appendChild(questionElement);
        });

        // Optional: Daten als JSON im Browser ausgeben
        console.log('Fetched Questions:', data);
    })
    .catch(error => {
        console.error('There was a problem with the fetch operation:', error);
    });