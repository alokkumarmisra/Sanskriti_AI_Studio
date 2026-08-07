#!/usr/bin/env python3
"""Clean up and fix recovery_manager.py"""

with open("ai_agents/scripts/recovery_manager.py", "r") as f:
    content = f.read()

# Find where the first main() ends (before duplicate starts)
first_main_end = content.find("\nif __name__ == \"__main__\":\n    main()\n")
duplicate_start = content.find("                    try:", first_main_end)

if duplicate_start > 0:
    # Cut off everything from duplicate_start to end
    clean_content = content[:duplicate_start]
    print(f"Removed {len(content) - len(clean_content)} bytes of duplicate content")
else:
    print("Could not find duplicate content marker")
    clean_content = content

# Now add the initialization for actions after printing status  
clean_content = clean_content.replace(
    '        print(f"[OK] Restored status: {status}")\n        ',
    '''        print(f"[OK] Restored status: {status}")
        
        # Initialize actions to avoid unbound variable error when history is empty/None
        actions: List[Any] = []
        '''
)

# Write back the fixed file
with open("ai_agents/scripts/recovery_manager.py", "w") as f:
    f.write(clean_content)

print("File cleaned and fixed!")
print("\nVerifying fix...")

with open("ai_agents/scripts/recovery_manager.py", "r") as f:
    content = f.read()

if "# Initialize actions to avoid unbound variable" in content:
    print("SUCCESS: 'actions' initialization added!")
else:
    print("WARNING: Fix may not have been applied correctly")

# Print relevant section
lines = content.split('\n')
for i, line in enumerate(lines[26:38], start=27):
    print(f"{i:3d} | {line}")
