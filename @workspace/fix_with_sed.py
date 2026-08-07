import re

# Read file
with open('ai_agents/scripts/debugger_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Use regex to fix the malformed pattern
# The broken line has: if not (not failure_report or )failure_report.get...
# We want: if not failure_report or not failure_report.get...

# Find all instances of the problematic pattern
pattern = r'if not\s*\(.*?failure_report\.get\("error_message"\):'
replacement = 'if not failure_report or not failure_report.get("error_message"):'

new_content = re.sub(pattern, replacement, content)

if new_content != content:
    print(f"Replaced {new_content.count('or not failure_report.get')} occurrence(s)")
    
    # Now ensure proper line break for the print statement
    broken_print = 'print("\\n[WARN] No error message provided. Debugging with minimal information.")        if'
    fixed_print = 'print("\\n[WARN] No error message provided. Debugging with minimal information.")\n'
    
    new_content = new_content.replace(broken_print, fixed_print)
    
    with open('ai_agents/scripts/debugger_agent.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Fix applied successfully!")
else:
    # Print what we have around the problematic area
    search = b'failure_report.get("error_message"):'
    with open('ai_agents/scripts/debugger_agent.py', 'rb') as f:
        content_bytes = f.read()
    
    pos = content_bytes.find(search)
    if pos != -1:
        start = max(0, pos - 50)
        end = min(len(content_bytes), pos + len(search) + 150)
        section = content_bytes[start:end]
        print(f"Context bytes:\n{section}")
