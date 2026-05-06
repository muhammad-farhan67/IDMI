**Indus Digital Market Intelligence (IDMI)** is a real-time intelligence platform purpose-built for Pakistan's digital economy. It tracks exchange rates, remote job market trends, and skill demand—synthesizing everything into actionable briefings powered by AI.

---

## 🧐 What is IDMI?
IDMI serves as a strategic compass for participants in Pakistan's digital workforce. It bridges the gap between raw global market data and the specific needs of local professionals, ensuring they have the insights required to thrive in a globalized economy.

## 👥 Who is it for?
* **Freelancers:** Pros on Upwork, Fiverr, and Toptal who need to identify the optimal time to convert USD/foreign earnings to PKR.
* **Remote Workers:** Professionals tracking global skill demand to stay competitive in the international market.
* **Digital Entrepreneurs:** Visionaries monitoring the pulse of Pakistan's evolving tech landscape.
* **Students:** New entrants using data-driven insights to guide their learning paths and career choices.

## ⚙️ How it Works
The platform operates on a fully automated intelligence cycle:

1.  **Data Pipeline:** A Python-based engine runs every 12 hours via GitHub Actions, scraping live exchange rates, job market shifts, and relevant news.
2.  **Storage & Access:** Data is stored in a Supabase (PostgreSQL) cloud database. The Streamlit frontend fetches this data with a 10-minute cache to ensure high performance and near-real-time accuracy.
3.  **STRATOS AI Engine:** Our proprietary AI analyst, **STRATOS**, processes the latest data snapshot to generate a concise, 3-sentence briefing. Each briefing covers:
    * **Currency Outlook:** Forecasts and trends for PKR.
    * **Job Market Trends:** Emerging opportunities in the global remote space.
    * **Actionable Recommendation:** A specific "move" for the day.

## 🛠 Tech Stack
* **Pipeline:** Python (Scheduled via GitHub Actions every 12 hours)
* **Database:** Supabase (PostgreSQL)
* **Frontend:** Streamlit (Multi-page Architecture)
* **Visualizations:** Plotly Express
* **AI Briefings:** Groq Cloud (Llama 3.3 70B Model)

---
