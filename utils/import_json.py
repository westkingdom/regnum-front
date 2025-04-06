import re
import json
import os

# File paths
input_file = "utils/group_map.json"
output_file = "utils/group_map_simplified.json"

def clean_json_file(input_file, output_file):
    # Read the malformed JSON file
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Extract the entries
    entries = []
    
    # Pattern to match an email followed by the details in malformed format
    pattern = r'"([^"]+@[^"]+)"\s*,\s*"{\s*"([^}]+)}'
    
    matches = re.findall(pattern, content)
    
    for match in matches:
        email = match[0]
        details_str = match[1]
        
        # Create a base entry with the email
        entry = {"email": email}
        
        # Extract other fields from details_str
        # Handle name field
        name_match = re.search(r'name"\s*:\s*"([^"]*)"', details_str)
        if name_match and name_match.group(1).strip():
            entry["name"] = name_match.group(1)
        else:
            # Fall back to generating a name from the email if name is not present or empty
            # Remove the domain part and format as a title
            local_part = email.split('@')[0]
            formatted_name = local_part.replace('-', ' ').replace('.', ' ').title()
            entry["name"] = formatted_name
            
        # Handle description field
        desc_match = re.search(r'description"\s*:\s*"([^"]*)"', details_str)
        if desc_match:
            entry["description"] = desc_match.group(1)
            
        # Handle id field
        id_match = re.search(r'id"\s*:\s*"([^"]*)"', details_str)
        if id_match:
            entry["id"] = id_match.group(1)
            
        # Handle type field - infer it from the email
        if any(keyword in email.lower() for keyword in [
            "-seneschal", "-marshal", "-archer", "-exchequer", 
            "-herald", "-chronicler", "-chatelaine", "-webminister",
            "-artssciences", "-baron", "-constable", "-regent", "-rapier"
        ]):
            entry["type"] = "officer"
        else:
            entry["type"] = "group"
            
        # Handle aliases field
        aliases_match = re.search(r'aliases"\s*:\s*\[(.*?)\]', details_str)
        if aliases_match:
            aliases_str = aliases_match.group(1)
            aliases = [alias.strip('"') for alias in re.findall(r'"([^"]*)"', aliases_str)]
            if aliases:
                entry["aliases"] = aliases
        
        # Handle nonEditableAliases field
        non_editable_aliases_match = re.search(r'nonEditableAliases"\s*:\s*\[(.*?)\]', details_str)
        if non_editable_aliases_match:
            non_editable_aliases_str = non_editable_aliases_match.group(1)
            non_editable_aliases = [alias.strip('"') for alias in re.findall(r'"([^"]*)"', non_editable_aliases_str)]
            if non_editable_aliases:
                entry["nonEditableAliases"] = non_editable_aliases
                
        # Add the entry to our list
        entries.append(entry)
    
    # Sort entries by name for better readability
    entries.sort(key=lambda x: x.get("name", ""))
    
    # Write the cleaned JSON to the output file
    with open(output_file, 'w') as f:
        json.dump(entries, f, indent=2)
    
    return len(entries)

try:
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    entry_count = clean_json_file(input_file, output_file)
    print(f"Successfully processed file. Extracted {entry_count} entries to {output_file}")
except Exception as e:
    print(f"An error occurred: {e}")