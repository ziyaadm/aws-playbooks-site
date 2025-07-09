import os
import json
import re
from datetime import datetime

# Define constants
PLAYBOOKS_DIR = "playbooks" 
OUTPUT_JSON_FILE = "playbooks.json"

def clean_title(filename):
    """
    Enhanced title parsing algorithm that cleans up messy filenames.
    Removes CE- prefix, timestamp suffixes, and formats properly.
    """
    # Remove file extension
    title = os.path.splitext(filename)[0]
    
    # Remove CE- prefix (case insensitive)
    title = re.sub(r'^CE-?', '', title, flags=re.IGNORECASE)
    
    # Remove timestamp patterns (e.g., -270623-230741, -DDMMYY-HHMMSS)
    title = re.sub(r'-\d{6}-\d{6}$', '', title)
    title = re.sub(r'-\d{8}-\d{6}$', '', title)
    
    # Remove (DRAFT) or (Draft) suffixes but keep track of them
    is_draft = bool(re.search(r'\(draft\)', title, re.IGNORECASE))
    title = re.sub(r'\s*\(draft\)\s*', '', title, flags=re.IGNORECASE)
    
    # Replace hyphens and underscores with spaces
    title = title.replace('-', ' ').replace('_', ' ')
    
    # Clean up multiple spaces
    title = re.sub(r'\s+', ' ', title).strip()
    
    # Proper title case but preserve certain words
    words = title.split()
    preserved_words = {'API', 'AWS', 'DNS', 'SSL', 'TLS', 'HTTP', 'HTTPS', 'URL', 'ID', 'IP'}
    
    title = ' '.join(word.upper() if word.upper() in preserved_words else word.capitalize() for word in words)
    
    return title, is_draft

def categorize_playbook(filename, title):
    """
    Categorizes playbooks based on filename and title content.
    Returns category and severity level.
    """
    title_lower = title.lower()
    filename_lower = filename.lower()
    
    # Define category keywords
    categories = {
        'Authentication': ['auth', 'login', 'credential', 'forbidden', 'unauthorized', '401', '403'],
        'Payment Processing': ['payment', 'merchant', 'authorize.net', 'braintree', 'funding', 'chargeback'],
        'Server Errors': ['500', '502', '503', '504', 'server error', 'internal error'],
        'API Issues': ['endpoint', 'api', 'webhook', 'preauth', 'callback'],
        'Notifications': ['notification', 'alert', 'email', 'metabase'],
        'Domain & SSL': ['domain', 'ssl', 'certificate', 'expire', 'verification'],
        'Data & Analytics': ['metabase', 'analytics', 'data', 'churn', 'merchant'],
        'Apple Pay': ['apple pay', 'apple']
    }
    
    # Determine category
    search_text = f"{title_lower} {filename_lower}"
    category = next((cat for cat, keywords in categories.items() 
                    if any(keyword in search_text for keyword in keywords)), 'General')
    
    # Determine severity based on keywords
    severity = 'Medium'
    if any(word in title_lower for word in ['critical', 'urgent', '500', '502', '503', '504']):
        severity = 'High'
    elif any(word in title_lower for word in ['warning', 'alert', 'notification', 'expire']):
        severity = 'Medium'
    elif any(word in title_lower for word in ['info', 'general', 'guide']):
        severity = 'Low'
    
    return category, severity

def extract_tags(title, filename):
    """
    Extracts relevant tags from the title and filename for better searchability.
    """
    tags = []
    
    # Common technical terms
    tech_terms = ['api', 'ssl', 'auth', 'payment', 'webhook', 'domain', 'email', 'notification', 
                  'error', 'alert', 'merchant', 'chargeback', 'credential', 'endpoint']
    
    search_text = f"{title.lower()} {filename.lower()}"
    tags.extend(term.upper() for term in tech_terms if term in search_text)
    
    # Add error codes as tags
    error_codes = re.findall(r'\b[45]\d{2}\b', title + ' ' + filename)
    tags.extend([f"HTTP {code}" for code in error_codes])
    
    # Add service names
    services = ['braintree', 'authorize.net', 'metabase', 'apple pay', 'vantiv']
    tags.extend(service.title() for service in services if service in search_text)
    
    return list(set(tags))  # Remove duplicates

def generate_playbooks_json():
    """
    Enhanced playbook JSON generation with better title parsing, categorization, and metadata.
    """
    playbooks_data = []

    # Construct the full path to the playbooks directory
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
        # Enhanced title parsing
        title, is_draft = clean_title(filename)
        
        # Categorization
        category, severity = categorize_playbook(filename, title)
        
        # Tag extraction
        tags = extract_tags(title, filename)
        
        # File path
        file_path = os.path.join(PLAYBOOKS_DIR, filename).replace(os.sep, '/')
        
        # Create enhanced playbook entry
        playbook_entry = {
            "title": title,
            "url": file_path,
            "category": category,
            "severity": severity,
            "tags": tags,
            "is_draft": is_draft,
            "filename": filename,
            "description": f"Troubleshooting guide for {title.lower()} issues and resolution steps."
        }
        
        playbooks_data.append(playbook_entry)
    
    # Sort by severity (High first), then by title
    severity_order = {'High': 0, 'Medium': 1, 'Low': 2}
    playbooks_data.sort(key=lambda x: (severity_order.get(x['severity'], 3), x['title']))
    
    try:
        output_json_path = os.path.join(current_script_dir, OUTPUT_JSON_FILE)
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(playbooks_data, f, indent=2)
        
        # Print summary with stats
        print(f"Successfully generated '{output_json_path}' with {len(playbooks_data)} playbooks.")
        
        # Print breakdowns
        from collections import Counter
        categories = Counter(p['category'] for p in playbooks_data)
        severities = Counter(p['severity'] for p in playbooks_data)
        
        print("\nCategory breakdown:")
        for cat, count in sorted(categories.items()):
            print(f"  {cat}: {count} playbooks")
        
        print("\nSeverity breakdown:")
        for sev, count in sorted(severities.items()):
            print(f"  {sev}: {count} playbooks")
            
    except IOError as e:
        print(f"Error writing to output file '{output_json_path}': {e}")

if __name__ == "__main__":
    generate_playbooks_json()

