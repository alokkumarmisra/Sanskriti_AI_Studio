# Directly write the corrected lines to the file
with open('ai_agents/scripts/vision_agent.py', 'r') as f:
    lines = f.readlines()

# Line 438 (index 437) - error pattern
lines[437] = '        (r"(?:error|fail)[,\\s]+([^\\n]+)", "errors")  # Simplified: single capturing group\n'

# Line 439 (index 438) - warning pattern
lines[438] = '        (r"(?:warning)[,\\s]+([^\\n]+)", "warnings")  # Simplified: single capturing group\n'

# Line 448 (index 447) - fix_pattern
lines[447] = '    fix_pattern = r"(?:recommend|suggest|fix)[,\\s]+([^\\n]+)"  # Simplified: single capturing group\n'

with open('ai_agents/scripts/vision_agent.py', 'w') as f:
    f.writelines(lines)

print('Lines updated successfully!')
print('- Line 438: error pattern simplified')
print('- Line 439: warning pattern simplified')  
print('- Line 448: fix_pattern simplified')
