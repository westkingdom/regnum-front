# filepath: /Users/xalg/dev/python/regnum-front/utils/pdata.py
import json
import os

# Load locations data from JSON file
try:
    with open(os.path.join(os.path.dirname(__file__), 'locations_data.json'), 'r') as f:
        locations_data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"Error loading locations data: {e}")
    # Fallback data in case the JSON file cannot be loaded
    locations_data = {
        "West Kingdom": ["Principality of the Mists", "Principality of Cynagua", "Principality of Oertha", "The Marches"]
    }
