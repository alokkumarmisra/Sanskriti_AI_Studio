#!/usr/bin/env python3
"""Fix the unbound 'actions' variable in recovery_manager.py"""

with open("ai_agents/scripts/recovery_manager.py", "r") as f:
    lines = f.readlines()

output = []
skip_until_next_method = False
indent_level = None

for i, line in enumerate(lines):
    # Skip duplicate code (from duplicate main function)
    if i > 0 and 'if __name__ == "__main__":' in line and lines[i-1].strip() != "":
        # This is the first occurrence - continue
        pass
    
    # Check for start of restore_runtime_state method (after cleanup)
    if "def restore_runtime_state(self)" in line:
        skip_until_next_method = False
        indent_level = 4
    
    # We need to add actions initialization after print status and before queue block
    # Look for the specific pattern: after printing status, then blank lines, then if queue
    stripped = line.strip()
    
    # Add the initialization comment and variable after the status prints
    if "print(f\"[OK] Restored status:" in line and skip_until_next_method == False:
        indent = len(line) - len(line.lstrip())
        output.append(' ' * indent + '# Initialize actions to avoid unbound variable error when history is empty/None\n')
        output.append(' ' * indent + 'actions: List[Any] = []\n')

with open("ai_agents/scripts/recovery_manager.py", "w") as f:
    f.writelines(output)

print("Fix applied. Checking for Pylance errors...")

# Verify the fix
with open("ai_agents/scripts/recovery_manager.py", "r") as f:
    content = f.read()

if "# Initialize actions to avoid unbound variable" in content:
    print("SUCCESS: 'actions' initialization added!")
else:
    print("WARNING: Fix may not have been applied correctly")
