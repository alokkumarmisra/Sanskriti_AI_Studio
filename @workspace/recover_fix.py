import re

# Read the corrupted file
with open('ai_agents/scripts/debugger_agent.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []  # Initialize outside the loop

# Find and fix the problematic line (line 1019, 0-indexed 1018)
for i in range(len(lines)):
    line = lines[i]
    if 'if not failure_report.get' in line and 'or not' in line:
        print(f"Found malformed line at {i+1}: {repr(line)}")
        # Fix this line by splitting it properly
        while i < len(lines):
            current = lines[i]
            if ':        print' in current and 'not failure_report or not' in current:
                # Split into two lines with proper indentation
                parts = current.split(':')
                if len(parts) == 2:
                    indent = len(current) - len(current.lstrip())
                    condition_line = current[:current.index(':')] + ':'
                    print_part = ':        print("\\n[WARN] No error message provided. Debugging with minimal information.")\n'
                    new_lines.append(indent * ' ' + condition_line + '\n')
                    new_lines.append((indent + 8) * ' ' + print_part.rstrip('\n'))
                    # Skip this line in the loop (we already added it)
                    continue
            new_lines.append(current)
            i += 1

# Write back
with open('ai_agents/scripts/debugger_agent.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Fix complete!")
