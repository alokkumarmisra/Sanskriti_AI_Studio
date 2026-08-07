#!/usr/bin/env python3
"""Script to fix the vision_agent.py file."""

# Read the original file
with open('ai_agents/scripts/vision_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Remove duplicate 'detected' in component pattern on line 414
old_pattern = r'(?:detected|found|identified|detected)\s*(?:components?|element)?[:,\s]+([^\n]+)'
new_pattern = r'(?:detected|found|identified)\s*(?:components?|element)?[:,\s]+([^\n]+)'

content = content.replace(old_pattern, new_pattern)

# Fix 2: Change assignment from list comprehension to append() method to properly handle type inference
old_assignment = 'result["detected_components"] = [comp_match.group(1).strip()]'
new_assignment = "result['detected_components'].append(comp_match.group(1).strip())"

content = content.replace(old_assignment, new_assignment)

# Write the fixed file
with open('ai_agents/scripts/vision_agent.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("File updated successfully!")

# Verify the changes
with open('ai_agents/scripts/vision_agent.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
print("\nLines 413-417:")
for i in range(412, min(417, len(lines))):
    print(f"{i+1} | {lines[i].rstrip()}")
