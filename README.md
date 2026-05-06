What is IDMI?
Indus Digital Market Intelligence is a real-time intelligence platform built for Pakistan's digital economy. It tracks exchange rates, remote job market trends, and skill demand — synthesising everything into actionable briefings powered by AI.

Who is it for?
Freelancers on Upwork, Fiverr, and Toptal who need to know the best time to convert earnings to PKR. Remote workers wanting to track which skills are most in demand globally. Digital entrepreneurs monitoring Pakistan's tech economy. Students entering the freelance market who want data to guide their learning path.

How it works
A data pipeline runs automatically every 12 hours, pulling live exchange rates, job market data, and news headlines from multiple sources. The data is stored in a cloud database and the Streamlit app reads from it in near-real-time, with a 10-minute cache.

An AI engine called STRATOS analyses the freshest snapshot and produces a concise 3-sentence briefing tailored to Pakistani freelancers — covering currency outlook, job market trends, and one actionable recommendation.

Tech Stack
Pipeline: Python, running on GitHub Actions (every 12 hours)
Database: Supabase (PostgreSQL)
Frontend: Streamlit multi-page app
Charts: Plotly Express
AI Briefings: Groq (Llama 3.3 70B)
