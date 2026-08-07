# Read raw bytes around line 1018 (0-indexed: 1017)
with open('ai_agents/scripts/debugger_agent.py', 'rb') as f:
    lines = f.readlines()

print("Lines 1015-1023 (0-indexed):")
for i in range(1015, min(1023, len(lines))):
    line = lines[i]
    print(f"{i+1}: {repr(line)}")
