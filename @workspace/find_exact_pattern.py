import re

# Read file as binary to preserve exact bytes
with open('ai_agents/scripts/debugger_agent.py', 'rb') as f:
    content = f.read()

# Find where the pattern exists
search_for = b'failure_report.get'
pos = content.find(search_for)
print(f"Position of 'failure_report.get': {pos}")

if pos != -1:
    # Get 200 bytes before and after with visible markers
    start = max(0, pos - 200)
    end = min(len(content), pos + len(search_for) + 200)
    section = content[start:end]
    
    # Replace newlines with markers for visibility
    section_visible = section.replace(b'\n', b'<<<NEWLINE>>>').replace(b'\r', b'<<<CARRIAGE>>')
    print(f"Bytes before target:\n{section_visible.decode('utf-8', errors='replace')}")
