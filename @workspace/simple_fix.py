import re

# Read the file as text to handle mixed encodings safely
with open('ai_agents/scripts/debugger_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Direct string replacement for the specific malformed line
old_text = 'if not failure_report or not failure_report.get("error_message"):        print("\\n[WARN] No error message provided. Debugging with minimal information.")'
new_text = '''    if not failure_report or not failure_report.get("error_message"):
        print("\\n[WARN] No error message provided. Debugging with minimal information.")'''

if old_text in content:
    new_content = content.replace(old_text, new_text)
    with open('ai_agents/scripts/debugger_agent.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Fix applied successfully!")
else:
    # Try alternative format (without leading spaces on first line of old_text)
    alt_old = '''if not failure_report or not failure_report.get("error_message"):        print("\\n[WARN] No error message provided. Debugging with minimal information.")'''
    if alt_old in content:
        new_content = content.replace(alt_old, new_text)
        with open('ai_agents/scripts/debugger_agent.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Alternative fix applied!")
    else:
        # Try without trailing spaces in the broken line
        alt_old2 = '''if not failure_report or not failure_report.get("error_message"):        print("\\n[WARN]'''
        if alt_old2 in content:
            new_content = content.replace(alt_old2, '''    if not failure_report or not failure_report.get("error_message"):
        print("\\n[WARN]''')
            with open('ai_agents/scripts/debugger_agent.py', 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("Alt 2 fix applied!")
        else:
            # Search for what we have
            search = 'failure_report.get("error_message")'
            pos = content.find(search)
            if pos != -1:
                start = max(0, pos - 50)
                end = min(len(content), pos + len(search) + 200)
                print(f"Context around '{search}':\n{repr(content[start:end])}")
            else:
                print("Pattern not found")
