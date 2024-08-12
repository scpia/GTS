fetch('/quiz')
    .then(response => response.json())
    
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
    });
