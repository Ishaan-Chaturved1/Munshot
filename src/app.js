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

async function loadData() {
  const [products, reviews, summaries] = await Promise.all([
    fetch("data/products.json").then((res) => res.json()),
    fetch("data/reviews.json").then((res) => res.json()),
    fetch("data/brand_summary.json").then((res) => res.json()),
  ]);

  state.products = products;
  state.reviews = reviews;
  state.summaries = summaries;
  state.filters.maxPrice = Math.max(...products.map((p) => p.price));
  state.filters.minRating = Math.min(...products.map((p) => p.rating));
  initControls();
  render();
}

function initControls() {
  const brands = [...new Set(state.products.map((p) => p.brand))].sort();
  const categories = [...new Set(state.products.map((p) => p.category))].sort();

  els.brandFilter.innerHTML = brands.map((brand) => `<option selected>${brand}</option>`).join("");
  state.filters.brands = brands;
  els.categoryFilter.insertAdjacentHTML(
    "beforeend",
    categories.map((category) => `<option>${category}</option>`).join(""),
  );

  const prices = state.products.map((p) => p.price);
  els.priceFilter.min = Math.floor(Math.min(...prices) / 500) * 500;
  els.priceFilter.max = Math.ceil(Math.max(...prices) / 500) * 500;
  els.priceFilter.value = els.priceFilter.max;
  state.filters.maxPrice = Number(els.priceFilter.value);

  els.ratingFilter.value = state.filters.minRating.toFixed(1);

  els.brandFilter.addEventListener("change", () => {
    state.filters.brands = [...els.brandFilter.selectedOptions].map((option) => option.value);
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
  els.productSelect.addEventListener("change", () => renderProductDetail(els.productSelect.value));
  document.querySelector("#resetFilters").addEventListener("click", resetFilters);
  document.querySelector("#exportCsv").addEventListener("click", exportComparisonCsv);
  document.querySelectorAll("#brandTable th[data-sort]").forEach((th) => {
    th.addEventListener("click", () => {
      const key = th.dataset.sort;
      const nextDirection = state.sort.key === key && state.sort.direction === "desc" ? "asc" : "desc";
      state.sort = { key, direction: nextDirection };
      renderBrandTable();
    });
  });
}

function resetFilters() {
  [...els.brandFilter.options].forEach((option) => {
    option.selected = true;
  });
  state.filters.brands = [...els.brandFilter.options].map((option) => option.value);
  els.categoryFilter.value = "all";
  els.sentimentFilter.value = "all";
  els.priceFilter.value = els.priceFilter.max;
  els.ratingFilter.value = els.ratingFilter.min;
  els.tableSearch.value = "";
  state.filters.category = "all";
  state.filters.sentiment = "all";
  state.filters.maxPrice = Number(els.priceFilter.value);
  state.filters.minRating = Number(els.ratingFilter.value);
  state.filters.search = "";
  render();
}

function filteredProducts() {
  return state.products.filter((product) => {
    const brandMatch = state.filters.brands.includes(product.brand);
    const categoryMatch = state.filters.category === "all" || product.category === state.filters.category;
    const priceMatch = product.price <= state.filters.maxPrice;
    const ratingMatch = product.rating >= state.filters.minRating;
    const sentimentMatch =
      state.filters.sentiment === "all" ||
      (state.filters.sentiment === "strong" && product.sentiment >= 75) ||
      (state.filters.sentiment === "mixed" && product.sentiment >= 60 && product.sentiment < 75) ||
      (state.filters.sentiment === "weak" && product.sentiment < 60);
    return brandMatch && categoryMatch && priceMatch && ratingMatch && sentimentMatch;
  });
}

function aggregateByBrand(products) {
  const groups = groupBy(products, (product) => product.brand);
  return [...groups.entries()].map(([brand, rows]) => {
    const reviewRows = state.reviews.filter((review) => rows.some((product) => product.product_id === review.product_id));
    const positives = topThemes(reviewRows, "positive");
    const negatives = topThemes(reviewRows, "negative");
    const avgPrice = average(rows, "price");
    const sentiment = average(reviewRows, "sentiment");
    return {
      brand,
      avgPrice,
      avgDiscount: average(rows, "discount_pct"),
      avgRating: average(rows, "rating"),
      reviewCount: rows.reduce((sum, product) => sum + product.review_count, 0),
      sampleReviews: reviewRows.length,
      sentiment,
      valueScore: sentiment / (avgPrice / 1000),
      topPros: positives,
      topCons: negatives,
      positioning: rows[0]?.positioning || "",
    };
  });
}

function average(rows, key) {
  if (!rows.length) return 0;
  return rows.reduce((sum, row) => sum + Number(row[key] || 0), 0) / rows.length;
}

function topThemes(rows, polarity) {
  const counts = rows
    .filter((row) => row.polarity === polarity)
    .reduce((acc, row) => acc.set(row.theme, (acc.get(row.theme) || 0) + 1), new Map());
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4)
    .map(([theme]) => theme);
}

function render() {
  const products = filteredProducts();
  const brands = aggregateByBrand(products);
  updateRangeLabels();
  renderMetrics(products, brands);
  renderInsights(brands);
  renderPositionChart(brands);
  renderDiscountChart(brands);
  renderBrandTable(brands);
  renderProductSelect(products);
}

function updateRangeLabels() {
  els.priceLabel.textContent = money.format(state.filters.maxPrice);
  els.ratingLabel.textContent = `${state.filters.minRating.toFixed(1)} stars`;
}

function renderMetrics(products, brands) {
  const reviews = state.reviews.filter((review) => products.some((product) => product.product_id === review.product_id));
  document.querySelector("#metricBrands").textContent = brands.length;
  document.querySelector("#metricProducts").textContent = products.length;
  document.querySelector("#metricReviews").textContent = number.format(reviews.length);
  document.querySelector("#metricSentiment").textContent = Math.round(average(reviews, "sentiment"));
}

function renderInsights(brands) {
  if (!brands.length) {
    els.insights.innerHTML = emptyState("No brands match the current filters.");
    return;
  }

  const sortedByValue = [...brands].sort((a, b) => b.valueScore - a.valueScore);
  const sortedByPremium = [...brands].sort((a, b) => b.avgPrice - a.avgPrice);
  const sortedByDiscount = [...brands].sort((a, b) => b.avgDiscount - a.avgDiscount);
  const sortedBySentiment = [...brands].sort((a, b) => b.sentiment - a.sentiment);
  const gap = [...brands].sort((a, b) => b.sentiment / b.avgDiscount - a.sentiment / a.avgDiscount);

  const insightRows = [
    {
      title: `${sortedByValue[0].brand} is strongest on value`,
      body: `${sortedByValue[0].brand} delivers ${Math.round(sortedByValue[0].sentiment)} sentiment at ${money.format(sortedByValue[0].avgPrice)}, the best sentiment-per-rupee signal in this view.`,
    },
    {
      title: `${sortedByPremium[0].brand} owns premium pricing`,
      body: `Average selling price is ${money.format(sortedByPremium[0].avgPrice)}, so its reviews need to justify the premium through durability and trust signals.`,
    },
    {
      title: `${sortedByDiscount[0].brand} leans most on discounts`,
      body: `A ${sortedByDiscount[0].avgDiscount.toFixed(1)}% average discount suggests demand may be promotion-sensitive.`,
    },
    {
      title: `${sortedBySentiment[0].brand} leads sentiment`,
      body: `Customers most often reward ${sortedBySentiment[0].brand} for ${sortedBySentiment[0].topPros.slice(0, 2).join(" and ")}.`,
    },
    {
      title: `${gap[0].brand} has efficient discounting`,
      body: `It converts discounting into sentiment better than peers, with fewer points of discount per sentiment point.`,
    },
  ];

  els.insights.innerHTML = insightRows
    .map((item) => `<article class="insight"><b>${item.title}</b><p>${item.body}</p></article>`)
    .join("");
}

function renderPositionChart(brands) {
  if (!brands.length) {
    els.positionChart.innerHTML = emptyState("No chart data.");
    return;
  }

  const prices = brands.map((brand) => brand.avgPrice);
  const sentiments = brands.map((brand) => brand.sentiment);
  const reviews = brands.map((brand) => brand.reviewCount);
  const minPrice = Math.min(...prices) * 0.94;
  const maxPrice = Math.max(...prices) * 1.06;
  const minSentiment = Math.min(...sentiments) * 0.96;
  const maxSentiment = Math.max(...sentiments) * 1.04;
  const maxReviews = Math.max(...reviews);

  const bubbles = brands
    .map((brand) => {
      const left = scale(brand.avgPrice, minPrice, maxPrice, 10, 90);
      const bottom = scale(brand.sentiment, minSentiment, maxSentiment, 12, 88);
      const size = scale(Math.sqrt(brand.reviewCount), 0, Math.sqrt(maxReviews), 54, 108);
      return `<button class="bubble" style="left:${left}%; bottom:${bottom}%; --size:${size}px" title="${brand.brand}: ${money.format(brand.avgPrice)}, ${Math.round(brand.sentiment)} sentiment" data-brand="${brand.brand}">
        ${brand.brand}<small>${Math.round(brand.sentiment)}</small>
      </button>`;
    })
    .join("");

  els.positionChart.innerHTML = `
    <span class="axis-label" style="left:12px; bottom:8px">Lower price</span>
    <span class="axis-label" style="right:12px; bottom:8px">Higher price</span>
    <span class="axis-label" style="left:12px; top:8px">Higher sentiment</span>
    ${bubbles}
  `;

  els.positionChart.querySelectorAll(".bubble").forEach((bubble) => {
    bubble.addEventListener("click", () => {
      [...els.brandFilter.options].forEach((option) => {
        option.selected = option.value === bubble.dataset.brand;
      });
      state.filters.brands = [bubble.dataset.brand];
      render();
    });
  });
}

function scale(value, min, max, outMin, outMax) {
  if (max === min) return (outMin + outMax) / 2;
  return outMin + ((value - min) / (max - min)) * (outMax - outMin);
}

function renderDiscountChart(brands) {
  const maxDiscount = Math.max(...brands.map((brand) => brand.avgDiscount), 1);
  els.discountChart.innerHTML = brands
    .sort((a, b) => b.avgDiscount - a.avgDiscount)
    .map(
      (brand) => `
        <div class="bar-row">
          <b>${brand.brand}</b>
          <span class="bar-track"><span class="bar-fill" style="--value:${(brand.avgDiscount / maxDiscount) * 100}%"></span></span>
          <span>${brand.avgDiscount.toFixed(1)}%</span>
        </div>
      `,
    )
    .join("");
}

function renderBrandTable(existingBrands) {
  const brands = existingBrands || aggregateByBrand(filteredProducts());
  const query = state.filters.search;
  const rows = brands
    .filter((brand) => {
      if (!query) return true;
      return `${brand.brand} ${brand.positioning} ${brand.topPros.join(" ")} ${brand.topCons.join(" ")}`.toLowerCase().includes(query);
    })
    .sort((a, b) => {
      const left = a[state.sort.key];
      const right = b[state.sort.key];
      const value = typeof left === "string" ? left.localeCompare(right) : left - right;
      return state.sort.direction === "asc" ? value : -value;
    });

  els.brandTableBody.innerHTML = rows
    .map(
      (brand) => `
      <tr>
        <td><b>${brand.brand}</b><br><span class="muted">${brand.positioning}</span></td>
        <td>${money.format(brand.avgPrice)}</td>
        <td>${brand.avgDiscount.toFixed(1)}%</td>
        <td>${brand.avgRating.toFixed(2)}</td>
        <td>${number.format(brand.reviewCount)}</td>
        <td><span class="score ${scoreClass(brand.sentiment)}">${Math.round(brand.sentiment)}</span></td>
        <td>${pills(brand.topPros)}</td>
        <td>${pills(brand.topCons)}</td>
      </tr>
    `,
    )
    .join("");
}

function pills(items) {
  return items.map((item) => `<span class="pill">${item}</span>`).join("");
}

function scoreClass(score) {
  if (score >= 74) return "good";
  if (score >= 60) return "warn";
  return "bad";
}

function renderProductSelect(products) {
  const sorted = [...products].sort((a, b) => a.brand.localeCompare(b.brand) || b.sentiment - a.sentiment);
  els.productSelect.innerHTML = sorted
    .map((product) => `<option value="${product.product_id}">${product.brand} - ${product.title}</option>`)
    .join("");
  renderProductDetail(sorted[0]?.product_id);
}

function renderProductDetail(productId) {
  const product = state.products.find((row) => row.product_id === productId);
  if (!product) {
    els.productDetail.innerHTML = emptyState("No products match the current filters.");
    return;
  }

  const reviews = state.reviews.filter((review) => review.product_id === product.product_id);
  const positive = topThemes(reviews, "positive");
  const negative = topThemes(reviews, "negative");
  const aspects = [...groupBy(reviews, (review) => review.aspect).entries()]
    .map(([aspect, rows]) => ({ aspect, sentiment: Math.round(average(rows, "sentiment")), count: rows.length }))
    .sort((a, b) => b.count - a.count);

  els.productDetail.innerHTML = `
    <article class="product-card">
      <h3>${product.title}</h3>
      <p>${product.positioning}</p>
      <div class="fact-grid">
        ${fact("Price", money.format(product.price))}
        ${fact("List price", money.format(product.list_price))}
        ${fact("Discount", `${product.discount_pct}%`)}
        ${fact("Rating", product.rating.toFixed(1))}
        ${fact("Review count", number.format(product.review_count))}
        ${fact("Sentiment", Math.round(average(reviews, "sentiment")))}
      </div>
    </article>
    <article class="product-card">
      <h3>Review synthesis</h3>
      <p>${synthesis(product, positive, negative)}</p>
      <div class="theme-columns">
        <div class="theme-box">
          <h4>Recurring praise</h4>
          <ul>${positive.map((item) => `<li>${item}</li>`).join("")}</ul>
        </div>
        <div class="theme-box">
          <h4>Recurring complaints</h4>
          <ul>${negative.map((item) => `<li>${item}</li>`).join("")}</ul>
        </div>
      </div>
      <div class="theme-box" style="margin-top:12px">
        <h4>Aspect-level sentiment</h4>
        ${aspects.map((item) => `<span class="pill">${item.aspect}: ${item.sentiment}</span>`).join("")}
      </div>
    </article>
  `;
}

function fact(label, value) {
  return `<div class="fact"><small>${label}</small><b>${value}</b></div>`;
}

function synthesis(product, positive, negative) {
  const mainPraise = positive.slice(0, 2).join(" and ") || "practical utility";
  const mainConcern = negative.slice(0, 2).join(" and ") || "post-purchase consistency";
  return `${product.brand} buyers mostly reward this product for ${mainPraise}. The risk to watch is ${mainConcern}, especially because it sits at ${money.format(product.price)} with a ${product.discount_pct}% listed discount.`;
}

function exportComparisonCsv() {
  const rows = aggregateByBrand(filteredProducts());
  const header = ["brand", "avgPrice", "avgDiscount", "avgRating", "reviewCount", "sentiment", "valueScore"];
  const csv = [header.join(",")]
    .concat(rows.map((row) => header.map((key) => JSON.stringify(row[key] ?? "")).join(",")))
    .join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "brand_comparison.csv";
  link.click();
  URL.revokeObjectURL(url);
}

function emptyState(message) {
  return `<p class="muted">${message}</p>`;
}

function groupBy(rows, getKey) {
  return rows.reduce((groups, row) => {
    const key = getKey(row);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(row);
    return groups;
  }, new Map());
}

loadData().catch((error) => {
  document.querySelector(".content").innerHTML = `
    <section class="panel">
      <h2>Dashboard could not load data</h2>
      <p>Run a local server from the project root, for example: <code>python -m http.server 8000</code>.</p>
      <pre>${error.message}</pre>
    </section>
  `;
});
