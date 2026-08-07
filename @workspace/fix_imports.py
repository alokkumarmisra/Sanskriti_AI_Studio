#!/usr/bin/env python3
"""Script to fix incorrect import paths in test file."""

import re

filepath = r"@workspace/ai_agents/tests/test_debugging_agent.py"

with open(filepath, 'r') as f:
    content = f.read()

# Fix all remaining "scripts.debugger_agent" imports to "debugger_agent"
# Pattern matches lines like: from scripts.debugger_agent import X
pattern1 = r'(from )scripts\.debugger_agent import (\w+)'
replacement1 = r'\g<1>debugger_agent import \g<2>'

content = re.sub(pattern1, replacement1, content)

# Also fix the patch decorators
pattern2 = r"@patch\(['\"]scripts\.debugger_agent\."
replacement2 = r"@patch('\g<0>"  # Keep scripts.debugger_agent for patch since it's using full module path
content = re.sub(pattern2, replacement2, content)

# But we also need to fix imports used inside @patch mocks - keep those as is since they're accessing module-level attributes

with open(filepath, 'w') as f:
    f.write(content)

print("Fixes applied. Checking for remaining issues...")
