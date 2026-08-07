import re

# Read the file
with open('ai_agents/scripts/vision_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix line 445 - change m[1] to m[0] (full match from re.findall)
content = content.replace('[m[1].strip()', '[m[0].strip()  # m[0] is full match')

# Fix line 451 - change f[1] to f[0] (full match from re.findall)  
content = content.replace('[f[1].strip()', '[f[0].strip()  # f[0] is full match')

# Also simplify the regex patterns to use single capturing group instead of nested groups
# This makes re.findall() return strings directly rather than tuples
old_error1 = r'(r"(?:error|fail)[,\s]+([\'\\"\[\]:(\w\s.]+\n?)+)", "errors")'
new_error1 = '(r"(?:error|fail)[,\s]+([^\\n]+)", "errors")'
content = content.replace(old_error1, new_error1)

old_error2 = r'(r"(?:warning)[,\s]+([\'\\"\[\]:(\w\s.]+\n?)+)", "warnings")'
new_error2 = '(r"(?:warning)[,\s]+([^\\n]+)", "warnings")'
content = content.replace(old_error2, new_error2)

old_fix_pattern = r'r"(?:recommend|suggest|fix)[,\s]+([\'\\"\[\]:(\w\s.]+\n?)+)"'
new_fix_pattern = r'r"(?:recommend|suggest|fix)[,\s]+([^\\n]+)"'
content = content.replace(old_fix_pattern, new_fix_pattern)

# Write the file back
with open('ai_agents/scripts/vision_agent.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('File updated with:')
print('  - Changed m[1] to m[0] (full match from re.findall)')
print('  - Changed f[1] to f[0] (full match from re.findall)')
print('  - Simplified regex patterns to use single capturing group')
