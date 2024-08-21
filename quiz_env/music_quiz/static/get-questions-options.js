const fetchCategories = async () => {
  try {
    // Lies die Kategorien aus der JSON-Datei
    const response = await fetch("/categories"); // Passe den Pfad an, wo die JSON-Datei gespeichert ist

    // Überprüfe, ob die Antwort erfolgreich war
    if (!response.ok) {
      throw new Error(`HTTP-Fehler! Status: ${response.status}`);
    }

    // Versuche, die JSON-Daten zu parsen
    const categories = await response.json();

    // Finde das Container-Element für das Menü
    const menuContainer = document.getElementById("categories-menu");

    // Stelle sicher, dass das Container-Element vorhanden ist
    if (!menuContainer) {
      throw new Error("Container für Kategorien-Menü nicht gefunden!");
    }

    // Leere den Container, bevor neue Daten hinzugefügt werden
    menuContainer.innerHTML = "";

    // Erstelle und füge die Schaltflächen für jede Kategorie hinzu
    categories.forEach((category) => {
      const button = document.createElement("a");
      button.href = `/quiz-fragen/${category.id}?category=${category.id}`;
      button.className = "menu-button";
      button.textContent = category.name;
      menuContainer.appendChild(button);
    });
  } catch (error) {
    console.error(
      "Fehler beim Abrufen oder Verarbeiten der Kategorien:",
      error
    );

    // Optional: Zeige eine Fehlermeldung auf der Webseite an
    const menuContainer = document.getElementById("categories-menu");
    if (menuContainer) {
      menuContainer.innerHTML = `<p>Es gab ein Problem beim Laden der Kategorien. Bitte versuche es später erneut.</p>`;
    }
  }
};

fetchCategories();
