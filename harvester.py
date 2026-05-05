import os
import requests
from supabase import create_client
import google.generativeai as genai
from datetime import datetime

# --- 1. SETUP CREDENTIALS (Securely loaded from environment) ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GEMINI_KEY = os.environ.get("GEMINI_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_KEY)

def run_ingestion_pipeline():
    print(f"[{datetime.now()}] Starting IDMI Ingestion Pipeline...")

    # --- 2. DATA HARVESTING (Variety & Velocity) ---
    # Fetch real USD to PKR rate
    response = requests.get("https://open.er-api.com/v6/latest/USD")
    pkr_rate = round(response.json()["rates"]["PKR"], 2)
    
    # Mocking live job data (In production, this scrapes Upwork/Rozee)
    # We use day of the month to simulate fluctuating job demand
    tech_jobs_volume = 1500 + (datetime.now().day * 15) 

    # --- 3. MARKET SENTIMENT NLP (Veracity) ---
    model = genai.GenerativeModel('gemini-2.0-flash')
    prompt = f"The current USD to PKR rate is {pkr_rate}. Based on this, write a 2-sentence market intelligence summary for Pakistani freelancers. Will hardware be expensive? Should they hold dollars?"
    ai_insight = model.generate_content(prompt).text

    # --- 4. BIG DATA STORAGE (Volume) ---
    data_payload = {
        "timestamp": datetime.now().isoformat(),
        "usd_pkr_rate": pkr_rate,
        "job_volume": tech_jobs_volume,
        "ai_sentiment": ai_insight,
        "purchasing_power_index": round(100000 / pkr_rate, 2) # How much $ you get for 100k PKR
    }
    
    # Insert into Supabase
    supabase.table("market_intel").insert(data_payload).execute()
    print("Pipeline Execution Complete. Data stored successfully.")

if __name__ == "__main__":
    run_ingestion_pipeline()
