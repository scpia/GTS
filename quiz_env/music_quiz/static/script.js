document.addEventListener("DOMContentLoaded", () => {
  // Lese die Kategorie-ID aus der URL
  const categoryId = new URLSearchParams(window.location.search).get("category") || "9"; // Standard auf Kategorie 9 (Allgemein)

  const apiUrl = `https://opentdb.com/api.php?amount=10&category=${categoryId}`;

  // Array zum Speichern der richtigen Antworten im globalen Scope
  window.correctAnswers = []; // Sicherstellen, dass es global ist

  // Funktion zur Verzögerung mit Promises
  const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));

  // Funktion zum Abrufen der Fragen
  const fetchQuestions = async () => {
    try {
      const response = await fetch(apiUrl); // Einmalig und dann muss man auch nicht 5 sekunden so warten 
      if (!response.ok) {
        const errorText = await response.text(); // Detaillierte Fehlermeldung
        throw new Error(
          `Network response was not ok. Status: ${response.status} ${response.statusText}. Response: ${errorText}`
        );
      }

      const data = await response.json();

      if (data.response_code === 5) {
        throw new Error("Invalid category ID or no questions available for this category.");
      }

      console.log("Fetched Questions Data:", data.results);
      displayQuestions(data.results);
    } catch (error) {
      console.error("Fehler beim Abrufen der Fragen:", error);
      alert(error.message); // Zeige eine benutzerfreundliche Nachricht an
    }
  };

  // Funktion zum Anzeigen der Fragen
  const displayQuestions = (questions) => {
    const container = document.getElementById("quiz-container");
    const quizTopic = document.getElementById("quiz-topic");

    if (!container) {
      console.error("Quiz container not found!");
      return;
    }

    // Setze das Thema dynamisch
    quizTopic.textContent = `Thema: ${questions[0].category}`;

    questions.forEach((question, index) => {
      window.correctAnswers[index] = question.correct_answer; // Speichere die richtige Antwort

      const questionElement = document.createElement("div");
      questionElement.className = "question";
      questionElement.innerHTML = `<p class="questions">${index + 1}. ${question.question}</p>`;

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
  };

  // Verzögerung vor dem Abrufen der Fragen
  const startFetching = async () => {
    console.log("Warte 5 Sekunden, bevor die Fragen abgerufen werden...");
    await wait(5000); // Warte 5 Sekunden
    await fetchQuestions(); // Dann Fragen abrufen
  };

  // Aufruf der Startfunktion
  startFetching();
});

// Funktion zur Validierung der Antworten
function validateForm() {
  let score = 0;
  const questions = document.querySelectorAll(".question");

  questions.forEach((question, index) => {
    // Überprüfen, ob eine Antwort ausgewählt wurde
    const selectedOption = question.querySelector('input[type="radio"]:checked');
    if (selectedOption) {
      if (selectedOption.value === window.correctAnswers[index]) {
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
