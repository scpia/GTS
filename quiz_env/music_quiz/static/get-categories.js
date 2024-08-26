const fs = require("fs");
const fetch = require("node-fetch");

const saveCategories = async () => {
  const response = await fetch("https://opentdb.com/api_category.php");
  const data = await response.json();
  const categories = data.trivia_categories;

  // Füge alle Kombinationsmöglichkeiten von Schwierigkeitsgrad und Fragetyp hinzu
  const difficulties = ["easy", "medium", "hard"];
  const types = ["multiple", "boolean"];

  const enrichedCategories = categories
    .map((category) => {
      return difficulties.flatMap((difficulty) =>
        types.map((type) => ({
          id: category.id,
          name: `${category.name} (${difficulty}, ${type})`,
          difficulty,
          type,
        }))
      );
    })
    .flat();

  // Speichere die angereicherten Kategorien in einer JSON-Datei
  fs.writeFileSync(
    "categories.json",
    JSON.stringify(enrichedCategories, null, 2)
  );
};

saveCategories()
  .then(() => {
    console.log("Kategorien erfolgreich gespeichert!");
  })
  .catch((err) => {
    console.error("Fehler beim Speichern der Kategorien:", err);
  });
