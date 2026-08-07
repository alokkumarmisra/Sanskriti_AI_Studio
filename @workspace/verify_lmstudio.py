import ast

# Parse the file directly with AST
with open('ai_agents/scripts/lmstudio_client.py', 'r') as f:
    source = f.read()
    
tree = ast.parse(source)

# Find LMStudioClient class
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef) and node.name == 'LMStudioClient':
        print(f"Found class: {node.name}")
        print(f"Number of body items: {len(node.body)}")
        for i, item in enumerate(node.body):
            if isinstance(item, ast.FunctionDef):
                print(f"  Method {i}: {item.name} at line {item.lineno}")
            elif isinstance(item, ast.AsyncFunctionDef):
                print(f"  AsyncMethod {i}: {item.name} at line {item.lineno}")

print("\n\n--- Raw source preview (first 60 lines) ---")
lines = source.split('\n')[:60]
for i, line in enumerate(lines):
    print(f"{i+1:3d}: {line}")
