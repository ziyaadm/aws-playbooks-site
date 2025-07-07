import os
import json

# Define constants
# IMPORTANT: Adjust this path if your 'playbooks' folder is not a sibling to this script.
# For your structure (aws-playbooks-site/infra/generate_json.py and aws-playbooks-site/infra/playbooks/)
# this 'playbooks' will work because 'playbooks' is relative to where generate_json.py is run.
PLAYBOOKS_DIR = "playbooks" 
OUTPUT_JSON_FILE = "playbooks.json"

def generate_playbooks_json():
    """
    Scans the 'playbooks/' directory for PDF files and creates a JSON manifest.
    Each entry in the JSON will contain the file path and a user-friendly title.
    """
    playbooks_data = []

    # Construct the full path to the playbooks directory relative to where the script is executed
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    full_playbooks_path = os.path.join(current_script_dir, PLAYBOOKS_DIR)

    if not os.path.exists(full_playbooks_path):
        print(f"Error: Playbooks directory '{full_playbooks_path}' not found.")
        print("Please ensure your PDF playbooks are inside a folder named 'playbooks' which is a sibling to this script, or adjust the PLAYBOOKS_DIR variable.")
        return

    playbook_files = [f for f in os.listdir(full_playbooks_path) if f.lower().endswith(".pdf")]
    
    if not playbook_files:
        print(f"Warning: No PDF files found in '{full_playbooks_path}'. '{OUTPUT_JSON_FILE}' will be empty.")

    playbook_files.sort()

    for filename in playbook_files:
        title = os.path.splitext(filename)[0].replace('-', ' ').replace('_', ' ').title()
        file_path = os.path.join(PLAYBOOKS_DIR, filename).replace(os.sep, '/') # Use forward slashes for URLs
        
        playbooks_data.append({
            "title": title,
            "url": file_path
        })
    
    try:
        output_json_path = os.path.join(current_script_dir, OUTPUT_JSON_FILE)
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(playbooks_data, f, indent=2)
        print(f"Successfully generated '{output_json_path}' with {len(playbooks_data)} playbooks.")
    except IOError as e:
        print(f"Error writing to output file '{output_json_path}': {e}")

if __name__ == "__main__":
    generate_playbooks_json()

