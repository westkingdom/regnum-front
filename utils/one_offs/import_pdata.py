import json

# The original locations_data dictionary
locations_data = {
    "West Kingdom": ["Principality of the Mists", "Principality of Cynagua", "Principality of Oertha", "The Marches"],
    "Cynagua": ["Shire of Bestwode", "Shire of Canale", "Shire of Champclair", "Shire of Belogor", "Shire of Danegeld Tor", "Shire of Fendrake Marsh", "Barony of Fettburg", "Province of Golden Rivers", "Shire of Mont d'Or", "Shire of Mountain's Gate", "Barony of Rivenoak", "Province of Silver Desert", "Shire of Thistletorr", "Shire of Vakkerfjell", "Shire of Windy Meads"],
    "Mists": ["Shire of Caldarium", "Shire of Cloondara", "Shire of Crosston", "Barony of Darkwood", "Canton of Caer Darth", "Canton of Hawk's Haven", "Canton of Montagne du Roi", "College of Saint David", "Province of the Mists", "College of Saint Katherine", "Province of Southern Shores", "Shire of Teufelberg", "Shire of Vinhold", "Barony of The Westermark", "Shire of Wolfscairn"],
    "Oertha": ["Shire of Earngyld", "Barony of Eskalya", "College of Saint Guinefort", "Shire of Hrafnafjordr", "Shire of Pavlok Gorod", "Barony of Selviergard", "Barony of Winter's Gate", "College of Saint Boniface"],
    "The Marches": ["Palatine Barony of Allyshia", "Shire of Ravenshore", "Shire of Wuduholt be Secg", "Barony of Tarnmist", "Canton of Borderwinds", "College of Saint Brendan", "Palatine Barony the Far West", "Canton of Golden Playne", "Stronghold of Battle Rock", "Stonghold of Eternal Winds", "Fortaleza de Islas de las Velas Latinas", "Stonghold Vale de Draco", "Stronghold of Warrior`s Gate"]
}

# Write to JSON file
with open('utils/locations_data.json', 'w') as json_file:
    json.dump(locations_data, json_file, indent=2)

print("JSON file created at utils/locations_data.json")

# Also create an updated pdata.py that loads from the JSON file
with open('utils/pdata.py', 'w') as py_file:
    py_file.write("""# filepath: /Users/xalg/dev/python/regnum-front/utils/pdata.py
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
""")

print("Updated pdata.py to load data from JSON file")