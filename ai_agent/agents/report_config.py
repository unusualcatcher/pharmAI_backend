import os

# Define the directory to save reports
REPORTS_DIR = 'reports'

# Create the directory if it doesn't exist
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(os.path.join(REPORTS_DIR, 'temp'), exist_ok=True)