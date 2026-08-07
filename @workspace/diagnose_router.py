import importlib.util
spec = importlib.util.spec_from_file_location('router', 'd:\\Sanskriti_AI_Studio\\ai_agents/communication_bus/router.py')

# Check if spec is valid before proceeding (spec can be None if file doesn't exist or has errors)
if spec:
    module = importlib.util.module_from_spec(spec)

    # Execute the module if it has a loader (only for .py files with valid syntax)
    if spec.loader:
        try:
            spec.loader.exec_module(module)

            # Check if Message exists in globals
            print(f"Message in dir: {'Message' in dir(module)}")
            print(f"Globals keys with Message: {[k for k in module.__dict__.keys() if 'Message' in k]}")
        except Exception as e:
            print(f"Error during execution: {e}")
            import traceback
            traceback.print_exc()
