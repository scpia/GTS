const fetchCategories = async () => {
  const response = await fetch("https://opentdb.com/api_category.php");
  const data = await response.json();
  const categories = data.trivia_categories;

  const menuContainer = document.getElementById("categories-menu");

  categories.forEach((category) => {
    const button = document.createElement("a");
    button.href = `/quiz-fragen/${category.id}?category=${category.id}`;
    button.className = "menu-button";
    console.log(category)
    button.textContent = category.name;
    menuContainer.appendChild(button);
  });
};

fetchCategories();
