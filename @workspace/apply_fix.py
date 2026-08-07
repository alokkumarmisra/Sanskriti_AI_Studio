import re

# Read the file
with open('ai_agents/scripts/vision_agent.py', 'r') as f:
    lines = f.readlines()

# Find and fix line 438 (0-indexed 437) - error pattern
for i, line in enumerate(lines):
    if '(r"(?:error|fail)[,\\s]+([\'"\[\]:(\\w\\s.]+\\n?)+)", "errors")' in line:
        lines[i] = line.replace(
            '(r"(?:error|fail)[,\\s]+([\'"\[\]:(\\w\\s.]+\\n?)+)", "errors")',
            '(r"(?:error|fail)[,\\s]+([^\\n]+)", "errors")  # Simplified: single capturing group'
        )
        print(f'Fixed line {i+1}: error pattern')

# Find and fix line 439 (0-indexed 438) - warning pattern
for i, line in enumerate(lines):
    if '(r"(?:warning)[,\\s]+([\'"\[\]:(\\w\\s.]+\\n?)+)", "warnings")' in line:
        lines[i] = line.replace(
            '(r"(?:warning)[,\\s]+([\'"\[\]:(\\w\\s.]+\\n?)+)", "warnings")',
            '(r"(?:warning)[,\\s]+([^\\n]+)", "warnings")  # Simplified: single capturing group'
        )
        print(f'Fixed line {i+1}: warning pattern')

# Find and fix line 448 (0-indexed 447) - fix_pattern
for i, line in enumerate(lines):
    if 'fix_pattern = r"(?:recommend|suggest|fix)[,\\s]+([\'"\[\]:(\\w\\s.]+\\n?)+)"' in line:
        lines[i] = line.replace(
            'fix_pattern = r"(?:recommend|suggest|fix)[,\\s]+([\'"\[\]:(\\w\\s.]+\\n?)+)"',
            'fix_pattern = r"(?:recommend|suggest|fix)[,\\s]+([^\\n]+)"  # Simplified: single capturing group'
        )
        print(f'Fixed line {i+1}: fix_pattern')

# Write the file back
with open('ai_agents/scripts/vision_agent.py', 'w') as f:
    f.writelines(lines)

print('\nAll regex patterns simplified to use single capturing group')
print('Lines 438-439 and 448 updated.')
