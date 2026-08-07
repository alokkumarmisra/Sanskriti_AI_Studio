with open('ai_agents/scripts/debugger_agent.py', 'r') as f:
    lines = f.readlines()

# Show the exact bytes for lines 1013-1021 (0-indexed: 1012-1020)
for i in range(1012, 1021):
    line = lines[i]
    # Replace common invisible chars with markers
    line_safe = line.replace('\t', '<<TAB>>').replace('\r', '<<<CR>>>')
    print(f'{i+1}: {repr(line_safe)}')
