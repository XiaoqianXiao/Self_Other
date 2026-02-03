"""
Usage
-----
1. Prepare files
   - Place matching `.log` and `.csv` files in the INPUT_DIR.
   - Each `.log` must have the same basename as its `.csv`.
     Example:
       sub-001_ses-01_run-01_*.log
       sub-001_ses-01_run-01_*.csv

2. Configure paths (if needed)
   - By default, INPUT_DIR is:
       <current_working_directory>/results
   - Output files will be written to:
       <current_working_directory>/results/summary
   - Modify INPUT_DIR and RESULTS_DIR at the top of the script if needed.

3. Run the script
   From the command line:
       python sum_results.py

4. Output
   - For each `.log`, a summary file is generated:
       <basename>_summary.csv
   - Output columns include:
       trial_no, onset_time, words, condition_name, valence,
       judgement, rt, responses, words_file, subID, sessionID, runID
    - Output Columns
    --------------
    trial_no : str
        Trial index

    onset_time : float (seconds)
        Stimulus onset time relative to the first scanner trigger ('t')

    words : str
        The stimulus word shown on that trial. 

    condition_name : str
        Experimental condition label 
        (e.g., SELF, OBAMA, UPPERCASE).

    valence : str or numeric
        Valence label  
        (e.g., positive/negative/neutral or numeric rating).

    judgement : str or numeric
        Participant’s judgement recorded if 
        - condition_name == 'UPPERCASE',
        - or the same as the condition_name.

    rt : float (seconds)
        - Reaction time if the participant responded with 'g' or 'r' after the stimulus onset and before the next stimulus onset.
        - Otherwise NaN.

    responses : str
        - Key pressed by the participant ('g' or 'r').
        - NaN if no valid response was detected.

    words_file : str
        Source file or stimulus list filename.

    subID : str
        Subject ID parsed from filename (sub-XXX).

    sessionID : str
        Session ID parsed from filename (ses-XXX).

    runID : str
        Run ID parsed from filename (run-XXX).

Notes
-----
- Onset times are relative to the first detected scanner trigger ('t').
- Valid responses are limited to 'g' and 'r'.
- Trials are matched using word identity (case-insensitive, FIFO order).
- If a trial has responses, then onset_time, rt, and responses will be set to NaN.
"""
import os
import re
import pandas as pd
import numpy as np
from collections import defaultdict, deque

# ================= USER SETTINGS =================
# Input: Where your current .log and .csv files are located
INPUT_DIR = os.path.join(os.getcwd(), 'results')

# Output: Where the summary files will be saved
RESULTS_DIR = os.path.join(os.getcwd(), 'results', 'summary')

# The exact columns to keep in the final output
FINAL_COLUMNS = [
    'trial_no', 'onset_time', 'words', 'condition_name', 
    'valence', 'judgement', 'rt', 'responses', 
    'words_file', 'subID', 'sessionID', 'runID'
]
# =================================================

def extract_ids_from_filename(filename):
    ids = {'subID': None, 'sessionID': None, 'runID': None}
    match = re.search(r'sub-([a-zA-Z0-9]+)_ses-([a-zA-Z0-9]+)_run-([a-zA-Z0-9]+)', filename)
    if match:
        ids['subID'] = match.group(1)
        ids['sessionID'] = match.group(2)
        ids['runID'] = match.group(3)
    return ids

def get_single_log(log_filename, input_dir, output_dir):
    log_path = os.path.join(input_dir, log_filename)
    csv_filename = log_filename.replace('.log', '.csv')
    csv_path = os.path.join(input_dir, csv_filename)
    
    print(f"--- Processing: {log_filename} ---")

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"   Error reading log file: {e}")
        return

    # Regex patterns
    # Captures text inside single quotes: text = 'WORD'
    text_pattern = re.compile(r"^([\d\.]+)\s+EXP\s+.*text = '(.+?)'")
    # Captures keypresses: Keypress: g
    key_pattern = re.compile(r"^([\d\.]+)\s+DATA\s+Keypress:\s+(\w)")

    # DATA STORE: Dictionary mapping 'lowercase_word' -> Queue of trial data
    # We use lowercase keys to ensure "ORIGINAL" matches "original"
    log_trial_map = defaultdict(deque)
    
    current_word = None
    stim_abs_onset = 0.0
    first_trigger_time = None
    
    # Configuration
    ignore_words = {'+', 'Please press', 'Hello World', 'default'}
    valid_conditions = {'SELF', 'OBAMA', 'UPPERCASE'}

    # --- PASS 1: Find Scanner Start (First 't') ---
    for line in lines:
        key_match = key_pattern.search(line)
        if key_match and key_match.group(2) == 't':
            first_trigger_time = float(key_match.group(1))
            break
    
    if first_trigger_time is None:
        print("   WARNING: No 't' detected. Using 0.0 as start time.")
        first_trigger_time = 0.0

    # --- PASS 2: Extract Data ---
    for line in lines:
        # Check for Text Stimuli
        text_match = text_pattern.search(line)
        if text_match:
            content = text_match.group(2).strip()
            timestamp = float(text_match.group(1))
            
            # Filter valid stimuli
            # We ignore instructions and condition labels
            if content not in ignore_words and content not in valid_conditions and not content.startswith('Please'):
                current_word = content
                stim_abs_onset = timestamp
                
                # Add a "placeholder" entry for this word occurrence
                # Key is LOWERCASE to handle case mismatches (e.g. UPPERCASE condition)
                key_word = current_word.lower()
                
                log_trial_map[key_word].append({
                    'onset_time': stim_abs_onset - first_trigger_time,
                    'responses': np.nan,
                    'rt': np.nan
                })

        # Check for Keypresses
        key_match = key_pattern.search(line)
        if key_match:
            key = key_match.group(2)
            timestamp = float(key_match.group(1))
            
            # If we found a valid key ('g' or 'r') and we are currently "in" a trial
            if key in ['g', 'r'] and current_word:
                if timestamp > stim_abs_onset:
                    rt = timestamp - stim_abs_onset
                    
                    # Update the LATEST entry in the queue for this word
                    key_word = current_word.lower()
                    
                    if log_trial_map[key_word]:
                        log_trial_map[key_word][-1]['responses'] = key
                        log_trial_map[key_word][-1]['rt'] = rt
                    
                    # Close the trial so we don't grab extra keys for the same word
                    current_word = None

    # 3. Read Original CSV
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        print(f"   ERROR: CSV not found ({csv_filename}). Skipping.")
        return

    # 4. Fill Metadata Columns if missing
    id_meta = extract_ids_from_filename(log_filename)
    for col in FINAL_COLUMNS:
        if col not in df.columns:
            df[col] = None

    if df['subID'].isnull().all() and id_meta['subID']: df['subID'] = id_meta['subID']
    if df['sessionID'].isnull().all() and id_meta['sessionID']: df['sessionID'] = id_meta['sessionID']
    if df['runID'].isnull().all() and id_meta['runID']: df['runID'] = id_meta['runID']

    # 5. Merge Data
    # Identify which column holds the word
    match_col = 'words'
    if 'words' not in df.columns and 'words_present' in df.columns:
        match_col = 'words_present'
    
    # Ensure output has a 'words' column
    if match_col != 'words':
        df['words'] = df[match_col]

    matched_count = 0
    
    for index, row in df.iterrows():
        raw_word = row.get(match_col)
        
        if pd.isna(raw_word):
            continue
            
        # Normalize CSV word to lowercase for matching
        target_key = str(raw_word).strip().lower()
        
        # Check if we have summary data for this word
        if target_key in log_trial_map and len(log_trial_map[target_key]) > 0:
            # POP the first occurrence from the queue (FIFO)
            log_info = log_trial_map[target_key].popleft()
            
            # Update the DataFrame
            df.at[index, 'onset_time'] = log_info['onset_time']
            df.at[index, 'responses'] = log_info['responses']
            df.at[index, 'rt'] = log_info['rt']
            matched_count += 1
        else:
            # No data found (word missing from log or queue empty)
            # Explicitly NaN out values to prevent stale data
            df.at[index, 'onset_time'] = np.nan
            df.at[index, 'responses'] = np.nan
            df.at[index, 'rt'] = np.nan

    # 6. Save Final Output
    try:
        df_final = df[FINAL_COLUMNS]
    except KeyError:
        existing_cols = [c for c in FINAL_COLUMNS if c in df.columns]
        df_final = df[existing_cols]

    output_filename = os.path.splitext(log_filename)[0] + '_summary.csv'
    output_path = os.path.join(output_dir, output_filename)
    
    df_final.to_csv(output_path, index=False)
    print(f"   Matched {matched_count}/{len(df)} trials.")
    print(f"   Saved to: {output_path}")

def process_all_logs():
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)

    files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.log')]
    
    if not files:
        print("No .log files found.")
        return

    for filename in files:
        get_single_log(filename, INPUT_DIR, RESULTS_DIR)

if __name__ == "__main__":
    process_all_logs()