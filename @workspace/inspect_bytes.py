with open('ai_agents/scripts/debugger_agent.py', 'rb') as f:
    content = f.read()

# Find position of the pattern
search_for = b'failure_report.get("error_message"):'
pos = content.find(search_for)

if pos != -1:
    # Get 100 bytes before and after
    start = max(0, pos - 100)
    end = min(len(content), pos + len(search_for) + 150)
    
    section = content[start:end]
    
    # Show each byte position with markers
    visible = []
    for i, b in enumerate(section):
        if b == ord('\n'):
            visible.append('<<NL>>')
        elif b == ord('\t'):
            visible.append('<<TAB>>')
        else:
            try:
                visible.append(chr(b))
            except:
                visible.append(f'#{b:#x}')
    
    print(''.join(visible))
else:
    print("Pattern not found")
