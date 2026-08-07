# Read the file
with open('ai_agents/scripts/vision_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix error_patterns - simplify regex to single capturing group
old_error1 = '(r"(?:error|fail)[,\\s]+([\'\\"\\[\\]:(\\w\\s.]+\\n?)+)", "errors")'
new_error1 = '(r"(?:error|fail)[,\\s]+([^\\n]+)", "errors")  # Simplified: single capturing group'
content = content.replace(old_error1, new_error1)

old_error2 = '(r"(?:warning)[,\\s]+([\'\\"\\[\\]:(\\w\\s.]+\\n?)+)", "warnings")'
new_error2 = '(r"(?:warning)[,\\s]+([^\\n]+)", "warnings")  # Simplified: single capturing group'
content = content.replace(old_error2, new_error2)

# Fix fix_pattern - simplify regex to single capturing group
old_fix_pattern = 'fix_pattern = r"(?:recommend|suggest|fix)[,\\s]+([\'\\"\\[\\]:(\\w\\s.]+\\n?)+)"'
new_fix_pattern = 'fix_pattern = r"(?:recommend|suggest|fix)[,\\s]+([^\\n]+)"  # Simplified: single capturing group'
content = content.replace(old_fix_pattern, new_fix_pattern)

# Write the file back
with open('ai_agents/scripts/vision_agent.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('File updated:')
print('  - error_patterns: simplified regex with single capturing group')
print('  - fix_pattern: simplified regex with single capturing group')
