// Fetch categories and populate dropdown
const fetchCategories = async () => {
  try {
    const response = await fetch("/categories");
    if (!response.ok) {
      throw new Error(`HTTP-Fehler! Status: ${response.status}`);
    }
    const categories = await response.json();
    const categorySelect = document.getElementById("category");

    categories.forEach((category) => {
      const option = document.createElement("option");
      option.value = category.id;
      option.textContent = category.name;
      categorySelect.appendChild(option);
    });
  } catch (error) {
    console.error("Fehler beim Abrufen der Kategorien:", error);
  }
};

// Apply filters and redirect to the questions page
const applyFilters = () => {
  const difficulty = document.getElementById("difficulty").value;
  const type = document.getElementById("type").value;
  const categoryId = document.getElementById("category").value;

  // Build the query string
  let query = "";
  if (difficulty) {
    query += `difficulty=${difficulty}&`;
  }
  if (type) {
    query += `type=${type}&`;
  }
  if (categoryId) {
    query += `category=${categoryId}&`;
  }

  // Remove trailing "&" if present
  if (query.endsWith("&")) {
    query = query.slice(0, -1);
  }

  // Redirect to the questions page with the filters applied
  window.location.href = `/quiz-fragen?${query}`;
};

document
  .getElementById("apply-filters")
  .addEventListener("click", applyFilters);

// Initialize categories dropdown on page load
fetchCategories();
