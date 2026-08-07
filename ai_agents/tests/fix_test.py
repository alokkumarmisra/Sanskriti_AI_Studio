#!/usr/bin/env python3
"""Fix test_communication_bus.py to add milestone_id parameter."""

with open('test_communication_bus.py', 'r') as f:
    content = f.read()

# Add milestone_id="" after task_id in the create_request call for test_message_serialization
old_text = '''    original = Message.create_request(
        source_agent="planner_agent",
        destination_agent="coding_agent",
        task_id="TASK-001",
        payload={"test": "data"},
    )'''

new_text = '''    original = Message.create_request(
        source_agent="planner_agent",
        destination_agent="coding_agent",
        task_id="TASK-001",
        milestone_id="",
        payload={"test": "data"},
    )'''

content = content.replace(old_text, new_text)

# Add assertion for milestone_id
old_asserts = '''    assert restored.task_id == original.task_id
    assert restored.payload == original.payload'''

new_asserts = '''    assert restored.task_id == original.task_id
    assert restored.milestone_id == original.milestone_id
    assert restored.payload == original.payload'''

content = content.replace(old_asserts, new_asserts)

with open('test_communication_bus.py', 'w') as f:
    f.write(content)

print("Fix applied successfully!")
