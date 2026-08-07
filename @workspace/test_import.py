import sys
sys.path.insert(0, 'd:\\Sanskriti_AI_Studio')

try:
    from ai_agents.communication_bus.router import Message, Router
    print("Import successful!")
    print(f"Message: {Message}")
    print(f"Router: {Router}")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
