const apiUrl = "https://opentdb.com/api.php?amount=10";

// Array zum Speichern der richtigen Antworten
let correctAnswers = [];

fetch(apiUrl)
  .then((response) => {
    if (!response.ok) {
      throw new Error("Network response was not ok");
    }
    return response.json(); // Die Antwort als JSON parsen
  })
  .then((data) => {
    const container = document.getElementById("quiz-container");
    if (!container) {
      console.error("Quiz container not found!");
      return;
    }

    data.results.forEach((question, index) => {
      correctAnswers[index] = question.correct_answer; // Speichere die richtige Antwort

      const questionElement = document.createElement("div");
      questionElement.className = "question";
      questionElement.innerHTML = `<p class="questions">${index + 1}. ${
        question.question
      }</p>`;

      // Antworten zusammenführen und mischen
      const allAnswers = [
        ...question.incorrect_answers,
        question.correct_answer,
      ];
      allAnswers.sort(() => Math.random() - 0.5); // Antworten zufällig mischen

      allAnswers.forEach((option) => {
        questionElement.innerHTML += `<input type="radio" name="q${index}" value="${option}"> ${option}<br>`;
      });

      container.appendChild(questionElement);
    });

    console.log("Fetched Questions:", data);
  })
  .catch((error) => {
    console.error("There was a problem with the fetch operation:", error);
  });

// Funktion zur Validierung der Antworten
function validateForm() {
  let score = 0;
  const questions = document.querySelectorAll(".question");

  questions.forEach((question, index) => {
    // Überprüfen, ob eine Antwort ausgewählt wurde
    const selectedOption = question.querySelector(
      'input[type="radio"]:checked'
    );
    if (selectedOption) {
      if (selectedOption.value === correctAnswers[index]) {
        score++;
        question.style.border = "2px solid green"; // Markiere die korrekten Antworten grün
      } else {
        question.style.border = "2px solid red"; // Markiere die falschen Antworten rot
      }
    } else {
      question.style.border = "2px solid orange"; // Markiere unbeantwortete Fragen orange
    }
  });

  // Zeige das Ergebnis an
  alert(`Du hast ${score} von ${questions.length} Fragen richtig beantwortet.`);
}
