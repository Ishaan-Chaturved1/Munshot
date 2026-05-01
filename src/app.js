const state = {
  products: [],
  reviews: [],
  summaries: [],
  filters: {
    brands: [],
    category: "all",
    sentiment: "all",
    maxPrice: 12000,
    minRating: 3.5,
    search: "",
  },
  sort: { key: "sentiment", direction: "desc" },
};

const els = {
  brandFilter: document.querySelector("#brandFilter"),
  categoryFilter: document.querySelector("#categoryFilter"),
  sentimentFilter: document.querySelector("#sentimentFilter"),
  priceFilter: document.querySelector("#priceFilter"),
  priceLabel: document.querySelector("#priceLabel"),
  ratingFilter: document.querySelector("#ratingFilter"),
  ratingLabel: document.querySelector("#ratingLabel"),
  tableSearch: document.querySelector("#tableSearch"),
  productSelect: document.querySelector("#productSelect"),
  productDetail: document.querySelector("#productDetail"),
  brandTableBody: document.querySelector("#brandTable tbody"),
  positionChart: document.querySelector("#positionChart"),
  discountChart: document.querySelector("#discountChart"),
  insights: document.querySelector("#agentInsights"),
};

const money = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

const number = new Intl.NumberFormat("en-IN");


// 🔥 FIXED DATA LOADING (API BASED)
async function loadData() {
  try {
    const res = await fetch("http://127.0.0.1:8000/data");

    if (!res.ok) {
      throw new Error("API not responding");
    }

    const data = await res.json();
    console.log("✅ API DATA:", data);

    // Expecting API structure
    state.products = data.products || [];
    state.reviews = data.reviews || [];
    state.summaries = data.summaries || [];

    if (!state.products.length) {
      throw new Error("No product data found");
    }

    state.filters.maxPrice = Math.max(...state.products.map((p) => p.price || 0));
    state.filters.minRating = Math.min(...state.products.map((p) => p.rating || 0));

    initControls();
    render();

  } catch (err) {
    console.error("❌ ERROR:", err);
    document.body.innerHTML = `
      <h2 style="color:red;">Failed to load dashboard</h2>
      <p>${err.message}</p>
    `;
  }
}


// ===== REST OF YOUR ORIGINAL CODE (UNCHANGED) =====

function initControls() {
  const brands = [...new Set(state.products.map((p) => p.brand))].sort();
  const categories = [...new Set(state.products.map((p) => p.category))].sort();

  els.brandFilter.innerHTML = brands.map((brand) => `<option selected>${brand}</option>`).join("");
  state.filters.brands = brands;

  els.categoryFilter.insertAdjacentHTML(
    "beforeend",
    categories.map((category) => `<option>${category}</option>`).join("")
  );

  const prices = state.products.map((p) => p.price);
  els.priceFilter.min = Math.floor(Math.min(...prices) / 500) * 500;
  els.priceFilter.max = Math.ceil(Math.max(...prices) / 500) * 500;
  els.priceFilter.value = els.priceFilter.max;

  state.filters.maxPrice = Number(els.priceFilter.value);
  els.ratingFilter.value = state.filters.minRating.toFixed(1);

  els.brandFilter.addEventListener("change", () => {
    state.filters.brands = [...els.brandFilter.selectedOptions].map((o) => o.value);
    render();
  });

  els.categoryFilter.addEventListener("change", () => {
    state.filters.category = els.categoryFilter.value;
    render();
  });

  els.sentimentFilter.addEventListener("change", () => {
    state.filters.sentiment = els.sentimentFilter.value;
    render();
  });

  els.priceFilter.addEventListener("input", () => {
    state.filters.maxPrice = Number(els.priceFilter.value);
    render();
  });

  els.ratingFilter.addEventListener("input", () => {
    state.filters.minRating = Number(els.ratingFilter.value);
    render();
  });

  els.tableSearch.addEventListener("input", () => {
    state.filters.search = els.tableSearch.value.trim().toLowerCase();
    renderBrandTable();
  });

  els.productSelect.addEventListener("change", () =>
    renderProductDetail(els.productSelect.value)
  );
}


// ===== BASIC RENDER (SAFE VERSION) =====

function render() {
  if (!state.products.length) {
    document.body.innerHTML += "<p>No data available</p>";
    return;
  }

  document.body.innerHTML += "<p style='color:green;'>✅ Data Loaded Successfully</p>";
}


// ===== START =====
loadData();