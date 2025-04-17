import json

# File paths
input_file = "utils/group_map_simplified.json"
output_file = "utils/group_map_filtered.json"

# Load the current JSON data
with open(input_file, 'r') as f:
    group_data = json.load(f)

# Filter out entries with 'legacy' in the email
filtered_data = [entry for entry in group_data if 'legacy' not in entry.get('email', '').lower()]

# Save the filtered data
with open(output_file, 'w') as f:
    json.dump(filtered_data, f, indent=2)

print(f"Original entries: {len(group_data)}")
print(f"Filtered entries: {len(filtered_data)}")
print(f"Removed {len(group_data) - len(filtered_data)} legacy entries")
print(f"Filtered data saved to {output_file}")