import re

# Read file
with open('ai_agents/scripts/debugger_agent.py', 'r') as f:
    content = f.read()

# Find and replace the broken line with correct code
broken_line = 'if not (not failure_report or )failure_report.get("error_message"):'
fixed_line = '    if not failure_report or not failure_report.get("error_message"):        print("\\n[WARN] No error message provided. Debugging with minimal information.")'

# Split into parts for easier replacement
parts = content.split(broken_line)
if len(parts) == 2:
    # Reconstruct with fixed line and proper indentation preserved
    old_section = '        if not failure_report.get("error_message"):\n        print("\\n[WARN] No error message provided. Debugging with minimal information.")'
    
    new_section = '    if not failure_report or not failure_report.get("error_message"):\n        print("\\n[WARN] No error message provided. Debugging with minimal information.")'
    
    fixed_content = content.replace(broken_line, '')
    # Fix the broken line and restore proper format
    temp = broken_line.split('\n', 1)
    if len(temp) == 2:
        indent = len(temp[0]) - len(temp[0].lstrip())
        new_line = ' ' * indent + 'if not failure_report or not failure_report.get("error_message"):        print("\\n[WARN] No error message provided. Debugging with minimal information.")'
        
        fixed_content = content.replace(
            '    if not (not failure_report or )failure_report.get("error_message"):',
            new_line
        )
        
        # Now fix the indentation of the print line
        old_print = '        print("\\n[WARN] No error message provided. Debugging with minimal information.")'
        new_indent = 8  # 8 spaces for the print line
        fixed_content = fixed_content.replace(
            '    if not failure_report or not failure_report.get("error_message"):\n        print("\\n[WARN] No error message provided. Debugging with minimal information.)',
            f'    if not failure_report or not failure_report.get("error_message"):\n{" " * new_indent}print("\\n[WARN] No error message provided. Debugging with minimal information.")'
        )
        
        # Simpler approach - just fix the malformed line directly
        fixed_content = fixed_content.replace(
            '    if not failure_report or not failure_report.get("error_message"):        print("\\n[WARN]',
            '    if not failure_report or not failure_report.get("error_message"):\n        print("\\n[WARN]"'
        )
        
        with open('ai_agents/scripts/debugger_agent.py', 'w') as f:
            f.write(fixed_content)
        print("Fix applied!")
    else:
        print("Could not split broken line correctly")
