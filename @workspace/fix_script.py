import re

# Read file as binary to preserve exact bytes
with open('ai_agents/scripts/debugger_agent.py', 'rb') as f:
    content = f.read()

# The exact pattern we need to replace (from the extract) - with newline handling
old_pattern = b'    if not\nfailure_report.get("error_message"):\n        print("\\n[WARN] No error message provided. Debugging with minimal information.")'

new_pattern = b'    if not failure_report or not failure_report.get("error_message"):\n        print("\\n[WARN] No error message provided. Debugging with minimal information.")'

if old_pattern in content:
    content = content.replace(old_pattern, new_pattern)
    
    with open('ai_agents/scripts/debugger_agent.py', 'wb') as f:
        f.write(content)
    print("Fix applied successfully!")
else:
    print("Pattern not found. Trying alternative...")


