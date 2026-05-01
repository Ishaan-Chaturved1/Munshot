# MUNSHOT internship assignment


A full-stack data pipeline that scrapes product data from e-commerce platforms, processes it using LLM-based analysis, and visualizes insights through an interactive dashboard.

---

## 🚀 Overview

This project automates the process of:

* Extracting product data from e-commerce websites
* Generating synthetic reviews
* Performing sentiment analysis using LLMs
* Transforming data into dashboard-ready format
* Visualizing insights in a web-based dashboard

It is designed to simulate a real-world **LLM Ops + Data Engineering pipeline**.

---

## ⚙️ Tech Stack

* **Python** – Data pipeline & scraping
* **Playwright** – Web scraping automation
* **JavaScript (Frontend)** – Dashboard visualization
* **LLMs (via API)** – Sentiment & insight generation
* **JSON** – Data storage & transformation

---

## 📂 Project Structure

```
munshot/
│
├── scripts/
│   ├── scrape_amazon_playwright.py
│   ├── generate_reviews.py
│   ├── llm_sentiments.py
│   ├── transform_to_dashboard_format.py
│   ├── generate_agent_insights.py
│
├── data/
│   ├── products.json
│   ├── reviews.json
│   ├── sentiments.json
│   ├── dashboard.json
│
├── dashboard/
│   ├── index.html
│   ├── app.js
│
└── README.md
```

---

## 🔄 Pipeline Flow

1. **Scraping**

   * Extract product details (title, price, rating, link)
   * Uses Playwright for browser automation

2. **Review Generation**

   * Synthetic reviews generated for each product

3. **Sentiment Analysis**

   * LLM processes reviews and assigns sentiment

4. **Data Transformation**

   * Converts raw data into dashboard-friendly format

5. **Insight Generation**

   * LLM creates high-level product insights

6. **Visualization**

   * Dashboard displays trends, ratings, and sentiment

---

## ▶️ How to Run

### 1. Scrape Products

```bash
python scripts/scrape_amazon_playwright.py --brands Safari Skybags Wildcraft "American Tourister" --max-products 3
```

### 2. Generate Reviews

```bash
python scripts/generate_reviews.py
```

### 3. Run Sentiment Analysis

```bash
python scripts/llm_sentiments.py
```

### 4. Transform Data

```bash
python scripts/transform_to_dashboard_format.py
```

### 5. Generate Insights

```bash
python scripts/generate_agent_insights.py
```

### 6. Start Dashboard

```bash
python -m http.server 8000
```

Then open:

```
http://localhost:8000/dashboard/
```

---

## 📊 Features

* 🔍 Multi-brand product scraping
* 🤖 LLM-based sentiment analysis
* 📈 Interactive dashboard
* 🔄 End-to-end automated pipeline
* 🧩 Modular and extensible architecture

---

## ⚠️ Limitations

* Amazon scraping may fail due to bot detection
* Requires stable internet connection
* LLM API usage may incur cost

---

## 💡 Future Improvements

* Add proxy rotation & stealth scraping
* Integrate real user reviews instead of synthetic
* Deploy dashboard online
* Add real-time data updates
* Expand to multiple e-commerce platforms

---

## 🎯 Use Case

* Demonstrates **LLM Ops pipeline design**
* Useful for **data engineering & AI portfolio projects**
* Showcases integration of scraping + AI + visualization

---

## 👨‍💻 Author

**Ishaan**
Computer Science Student

---

## ⭐ If you like this project

Give it a star and use it as inspiration for your own AI pipelines!
