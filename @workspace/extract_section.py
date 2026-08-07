with open('ai_agents/scripts/debugger_agent.py', 'rb') as f:
    content_bytes = f.read()

# Find position of the problematic pattern
target = b'if not failure_report.get("error_message"):'
pos = content_bytes.find(target)

if pos != -1:
    # Get 200 bytes before and after
    start = max(0, pos - 200)
    end = min(len(content_bytes), pos + len(target) + 200)
    section = content_bytes[start:end]
    print(section.decode('utf-8', errors='replace'))
else:
    print("Target pattern not found!")
