import requests
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# --- SECURE CONFIGURATION (Pulls from hidden GitHub Secrets) ---
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

# --- CONFIGURATION (CLOUD COMPATIBLE) ---
# Saves the tracking file directly inside your repository directory
SEEN_JOBS_FILE = os.path.join(os.path.dirname(__file__), "seen_jobs.json")

# Your Target Companies
COMPANIES = [
    "Rivian", "Lucid", "Canoo", "Tesla", 
    "Slate", "Ferrari", "Porsche", "McLaren", "Ford", "GM", "Kia", 
    "Toyota", "Honda", "Hyundai", "BMW", "Mercedes Benz", "Audi", 
    "Suzuki", "Volkswagen", "Nissan", "Subaru", "Mazda", "Volvo", 
    "Polestar", "Jaguar", "Land Rover", "Mitsubishi", "Stellantis"
]

COMPANY_ALIASES = {
    "ECR": "Ed Carpenter Racing",
    "GM": "General Motors"
}

# Your Target Keywords
QUERY_KEYWORDS = '"testing" OR "aerodynamics" OR "aero" OR "validation" OR "hardware in the loop" OR "wind tunnel" OR "trackside" OR "hands-on"'

def load_seen_jobs():
    if not os.path.exists(SEEN_JOBS_FILE):
        return set()
    try:
        with open(SEEN_JOBS_FILE, 'r') as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_seen_jobs(seen_jobs):
    os.makedirs(os.path.dirname(SEEN_JOBS_FILE), exist_ok=True)
    with open(SEEN_JOBS_FILE, 'w') as f:
        json.dump(list(seen_jobs), f)

def search_jobs(company_name):
    if not RAPIDAPI_KEY:
        print("Missing RapidAPI Key!")
        return []
        
    search_company = COMPANY_ALIASES.get(company_name, company_name)
    url = "https://jsearch.p.rapidapi.com/search-v2" 
    
    querystring = {
        "query": f"{search_company} {QUERY_KEYWORDS} internship OR co-op",
        "page": "1",
        "num_pages": "1"
    }
    
    # We add a fake web browser User-Agent so GitHub runners bypass firewalls
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        
        # This logs a clear error if your API key token count runs out
        if response.status_code != 200:
            print(f"API Error for {search_company}: Status Code {response.status_code} - Reason: {response.text[:100]}")
            return []
            
        payload = response.json()
        data = payload.get('data', {})
        return data.get('jobs', []) if isinstance(data, dict) else []
        
    except Exception as e:
        print(f"Error searching {search_company}: {e}")
        return []

def send_email(new_jobs):
    if not new_jobs:
        return 
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("Missing email credentials! Cannot send report.")
        return

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL or SENDER_EMAIL
    msg['Subject'] = f"🚨 New Aero/Testing Internships Found ({len(new_jobs)} new)"

    body = "Here are the new internship/co-op postings matching your criteria:\n\n"
    for job in new_jobs:
        company = job.get('employer_name', 'Unknown company')
        title = job.get('job_title', 'Untitled position')
        city = job.get('job_city', '')
        state = job.get('job_state', '')
        location = ', '.join(part for part in (city, state) if part) or 'Location not provided'
        link = job.get('job_apply_link', 'No application link provided')
        body += f"• **{company}** - {title}\n"
        body += f"  Location: {location}\n"
        body += f"  Link: {link}\n\n"

    msg.attach(MIMEText(body, 'plain'))

    try:
        # We switch to SMTP_SSL on Port 465 which is cleaner for cloud runners bypassing DNS bugs
        server = smtplib.SMTP_SSL('://gmail.com', 465, timeout=15)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Standard connection failed: {e}. Trying fallback...")
        try:
            # Fallback to standard TLS port 587 if SSL is restricted
            server = smtplib.SMTP('://gmail.com', 587, timeout=15)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            server.quit()
            print("Email sent successfully via fallback!")
        except Exception as fallback_error:
            print(f"Failed to send email entirely: {fallback_error}")


def main():
    seen_jobs = load_seen_jobs()
    new_jobs_list = []

    print("Starting job scrape...")
    for company in COMPANIES:
        print(f"Checking {company}...")
        results = search_jobs(company)
        
        for job in results:
            job_id = job.get('job_id')
            if job_id and job_id not in seen_jobs:
                seen_jobs.add(job_id)
                new_jobs_list.append(job)
    
    save_seen_jobs(seen_jobs)
    
    if new_jobs_list:
        print(f"Found {len(new_jobs_list)} new jobs! Sending report...")
        send_email(new_jobs_list)
    else:
        print("No new jobs found today.")

if __name__ == "__main__":
    main()
