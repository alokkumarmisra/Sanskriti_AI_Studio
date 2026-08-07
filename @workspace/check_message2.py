# Read file and check for Message class content
with open('d:\\Sanskriti_AI_Studio\\ai_agents\\communication_bus\\router.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
for i, line in enumerate(lines[65:90], start=66):  # Check around lines 66-90
    print(f"{i}|{line.rstrip()}")
