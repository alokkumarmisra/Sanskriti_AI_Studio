import ast

with open('d:\\Sanskriti_AI_Studio\\ai_agents\\communication_bus\\router.py', 'r', encoding='utf-8') as f:
    source = f.read()

try:
    tree = ast.parse(source)
    print("AST parsing: SUCCESS")
    
    # Find all classes in the file
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            print(f"Found class: {node.name} at line {node.lineno}")
            
except SyntaxError as e:
    print(f"Syntax error at line {e.lineno}: {e.msg}")
