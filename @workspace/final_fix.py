import re

# Read file
with open('ai_agents/scripts/debugger_agent.py', 'r') as f:
    content = f.read()

# Use regex substitution to fix the pattern
# Match: if not failure_report.get("error_message"): followed by the print line
pattern = r'(    if not )failure_report\.get\("error_message"\):'
replacement = r'\1(not failure_report or )failure_report.get("error_message"):'

new_content = re.sub(pattern, replacement, content)

if new_content != content:
    with open('ai_agents/scripts/debugger_agent.py', 'w') as f:
        f.write(new_content)
    print("Fix applied successfully!")
else:
    print("Pattern not found")
