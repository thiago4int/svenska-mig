const categoryList = document.getElementById("categoryList");
const sidebar = document.getElementById("sidebar");
const menuToggle = document.getElementById("menuToggle");
const card = document.getElementById("card");
const frontText = document.getElementById("frontText");
const frontTranslation = document.getElementById("frontTranslation");
const backText = document.getElementById("backText");
const progress = document.getElementById("progress");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const shuffleBtn = document.getElementById("shuffleBtn");
const resetBtn = document.getElementById("resetBtn");
const tabFlashcards = document.getElementById("tabFlashcards");
const tabWordList = document.getElementById("tabWordList");
const flashcardsPanel = document.getElementById("flashcardsPanel");
const wordListPanel = document.getElementById("wordListPanel");
const wordListContent = document.getElementById("wordListContent");

const ALL_CATEGORY = "All words";

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[c]));
}

let deck = [];
let index = 0;

function buildDeck(categoryName) {
  if (categoryName === ALL_CATEGORY) {
    return FLASHCARD_DATA.flatMap((group) => group.words);
  }
  const group = FLASHCARD_DATA.find((g) => g.category === categoryName);
  return group ? [...group.words] : [];
}

function shuffleArray(arr) {
  const copy = [...arr];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

function populateCategories() {
  const names = [ALL_CATEGORY, ...FLASHCARD_DATA.map((g) => g.category)];
  categoryList.innerHTML = names
    .map((name) => `<li><button type="button" data-category="${name}">${name}</button></li>`)
    .join("");
}

function setActiveCategory(categoryName) {
  categoryList.querySelectorAll("button").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.category === categoryName);
  });
}

function showCard() {
  card.classList.remove("flipped");
  const current = deck[index];
  if (!current) {
    frontText.textContent = "No words in this category";
    frontTranslation.textContent = "";
    backText.textContent = "";
    progress.textContent = "";
    return;
  }
  frontText.textContent = current.sv;
  frontTranslation.textContent = current.en;
  backText.textContent = current.en;
  progress.textContent = `${index + 1} / ${deck.length}`;
}

function wordTableHtml(words) {
  const rows = words
    .map(
      (w) => `<tr>
        <td class="sv-cell">${escapeHtml(w.sv)}</td>
        <td class="type-cell">${escapeHtml(w.type || "—")}</td>
        <td>${escapeHtml(w.en)}</td>
        <td class="forms-cell">${escapeHtml(w.forms || "—")}</td>
      </tr>`
    )
    .join("");
  return `<div class="word-table-wrap">
    <table class="word-table">
      <thead>
        <tr><th>Swedish</th><th>Type</th><th>English</th><th>Other forms</th></tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  </div>`;
}

function renderWordList(categoryName) {
  if (categoryName === ALL_CATEGORY) {
    wordListContent.innerHTML = FLASHCARD_DATA.map(
      (group) => `<div class="word-list-category">
        <h2>${escapeHtml(group.category)}</h2>
        ${wordTableHtml(group.words)}
      </div>`
    ).join("");
    return;
  }
  const group = FLASHCARD_DATA.find((g) => g.category === categoryName);
  wordListContent.innerHTML = group ? wordTableHtml(group.words) : "";
}

function goTo(newIndex) {
  if (deck.length === 0) return;
  index = (newIndex + deck.length) % deck.length;
  showCard();
}

let currentCategory = ALL_CATEGORY;

function loadCategory(categoryName) {
  currentCategory = categoryName;
  deck = buildDeck(categoryName);
  index = 0;
  setActiveCategory(categoryName);
  showCard();
  renderWordList(categoryName);
  sidebar.classList.remove("open");
  menuToggle.setAttribute("aria-expanded", "false");
}

function setView(view) {
  const isFlashcards = view === "flashcards";
  flashcardsPanel.hidden = !isFlashcards;
  wordListPanel.hidden = isFlashcards;
  tabFlashcards.classList.toggle("active", isFlashcards);
  tabWordList.classList.toggle("active", !isFlashcards);
  tabFlashcards.setAttribute("aria-selected", String(isFlashcards));
  tabWordList.setAttribute("aria-selected", String(!isFlashcards));
}

card.addEventListener("click", () => card.classList.toggle("flipped"));
card.addEventListener("keydown", (e) => {
  if (e.code === "Space") {
    e.preventDefault();
    card.classList.toggle("flipped");
  }
});

prevBtn.addEventListener("click", () => goTo(index - 1));
nextBtn.addEventListener("click", () => goTo(index + 1));

shuffleBtn.addEventListener("click", () => {
  deck = shuffleArray(deck);
  index = 0;
  showCard();
});

resetBtn.addEventListener("click", () => loadCategory(currentCategory));

categoryList.addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-category]");
  if (btn) loadCategory(btn.dataset.category);
});

menuToggle.addEventListener("click", () => {
  const isOpen = sidebar.classList.toggle("open");
  menuToggle.setAttribute("aria-expanded", String(isOpen));
});

tabFlashcards.addEventListener("click", () => setView("flashcards"));
tabWordList.addEventListener("click", () => setView("list"));

populateCategories();
loadCategory(ALL_CATEGORY);
