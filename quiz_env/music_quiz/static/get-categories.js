// saveCategories.js
const fs = require("fs");
const fetch = require("node-fetch");

const saveCategories = async () => {
  const response = await fetch("https://opentdb.com/api_category.php");
  const data = await response.json();
  const categories = data.trivia_categories;

  // Speichere die Kategorien in einer JSON-Datei
  fs.writeFileSync("categories.json", JSON.stringify(categories, null, 2));
};

saveCategories()
  .then(() => {
    console.log("Kategorien erfolgreich gespeichert!");
  })
  .catch((err) => {
    console.error("Fehler beim Speichern der Kategorien:", err);
  });
