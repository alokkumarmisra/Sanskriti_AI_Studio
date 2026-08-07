with open('ai_agents/scripts/debugger_agent.py', 'r') as f:
    lines = f.readlines()
    
for i, line in enumerate(lines[1012:1030], start=1013):
    print(f'{i}: {repr(line)}')
