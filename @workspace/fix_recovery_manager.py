#!/usr/bin/env python3
"""Fix the unbound 'actions' variable in recovery_manager.py"""

import re
import os

with open("ai_agents/scripts/recovery_manager.py", "r") as f:
    content = f.read()

# Remove duplicate code (everything after first occurrence of restore_runtime_state method)
# Find the first restore_runtime_state method and keep everything up to its closing brace,
# then find verify_environment_before_resume and keep everything from there

first_method_end = content.find('def restore_runtime_state(self) -> Dict[str, Any]:')
second_method_start = content.find('\n    def handle_failure(self', first_method_end)
if second_method_start == -1:
    second_method_start = content.find('\ndef main() -> None:', first_method_end)

# Keep from start up to the first method's closing brace (before verify_environment_before_resume)
# Find where restore_runtime_state ends (find next def at same indentation level or end of class)
class_end = content.rfind('# =============================================================================\n# RECOVERY MANAGER')
first_class_start = content.find('\nclass RecoveryManager:', class_end)

if first_method_end > 0 and second_method_start > 0:
    # Find the end of restore_runtime_state (next method at same indent or blank line + different section)
    pattern = r'(    def restore_runtime_state\(self\) -> Dict\[str, Any\]:.*?)(    def verify_environment_before_resume)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        first_method_content = match.group(1)
        rest_of_file = match.group(2) + content[match.end():]
        clean_content = first_method_content + "\n\n" + rest_of_file
        print(f"Removed {len(content) - len(clean_content)} bytes of duplicate content")
    else:
        print("Could not find pattern to remove duplicates")
        clean_content = content
else:
    print("Could not locate method boundaries")
    clean_content = content

# Write back the cleaned file
with open("ai_agents/scripts/recovery_manager.py", "w") as f:
    f.write(clean_content)

print("File cleaned. Now applying fix for 'actions' variable initialization...")

# Now add the initialization for actions before it's used in return statement
target_pattern = r'(        print\(f"\[OK\] Restored status: \{status\}"\)\n\n        if queue:\n            print\(f"\[OK\] Restored queue with \{len\(queue\)} tasks"\)\n\n        if history:\n)(            actions = history\.get\("actions", \[\]\) or \[\])'

replacement = r'''\1        # Initialize actions to avoid unbound variable error when history is empty/None
        actions: List[Any] = []

\2'''

new_content = re.sub(target_pattern, replacement, clean_content, flags=re.DOTALL)

# Write back the fixed file
with open("ai_agents/scripts/recovery_manager.py", "w") as f:
    f.write(new_content)

print("Fix applied. Verifying...")

# Verify the fix was applied
if "Initialize actions to avoid unbound variable error" in new_content:
    print("SUCCESS: 'actions' initialization added successfully!")
else:
    print("WARNING: Could not verify fix was applied")

# Print the relevant section for verification
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
from ai_agents import scripts

print("\nFix complete. You can now check the file in VS Code.")
