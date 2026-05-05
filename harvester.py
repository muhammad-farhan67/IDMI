import os
import requests
from supabase import create_client
from groq import Groq  # Swapped from google.generativeai
from datetime import datetime

# --- 1. SETUP CREDENTIALS ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") # Use the Groq Key name

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
# Initialize Groq Client
groq_client = Groq(api_key=GROQ_API_KEY)

def run_ingestion_pipeline():
    print(f"[{datetime.now()}] Starting IDMI Ingestion Pipeline...")

    # --- 2. DATA HARVESTING ---
    response = requests.get("https://open.er-api.com/v6/latest/USD")
    pkr_rate = round(response.json()["rates"]["PKR"], 2)
    
    tech_jobs_volume = 1500 + (datetime.now().day * 15) 

    # --- 3. MARKET SENTIMENT NLP (Using Groq LPU for Speed) ---
    prompt = f"The current USD to PKR rate is {pkr_rate}. Based on this, write a 2-sentence market intelligence summary for Pakistani freelancers. Will hardware be expensive? Should they hold dollars?"
    
    # Swapped Gemini call for Groq Chat Completion
    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a professional market analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=150
    )
    ai_insight = completion.choices[0].message.content

    # --- 4. BIG DATA STORAGE ---
    data_payload = {
        "timestamp": datetime.now().isoformat(),
        "usd_pkr_rate": pkr_rate,
        "job_volume": tech_jobs_volume,
        "ai_sentiment": ai_insight,
        "purchasing_power_index": round(100000 / pkr_rate, 2)
    }
    
    # Insert into Supabase
    supabase.table("market_intel").insert(data_payload).execute()
    print("Pipeline Execution Complete. Data stored successfully.")

if __name__ == "__main__":
    run_ingestion_pipeline()
