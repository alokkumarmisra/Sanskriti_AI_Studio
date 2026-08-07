import sys
sys.path.insert(0, '.')

# Fresh import with explicit reload
if 'ai_agents.scripts.lmstudio_client' in sys.modules:
    del sys.modules['ai_agents.scripts.lmstudio_client']
if 'ai_agents.scripts' in sys.modules:
    del sys.modules['ai_agents.scripts']

from ai_agents.scripts import LMStudioClient
print(f"Class name: {LMStudioClient.__name__}")

# Check what methods are defined in the class source
import inspect
try:
    src = inspect.getsource(LMStudioClient)
    lines = src.split('\n')
    print(f"Source lines: {len(lines)}")
    
    # Find method definitions
    for i, line in enumerate(lines[:100]):  # First 100 lines
        if 'def ' in line and not line.strip().startswith('"""'):
            print(f"  Line {i+1}: {line.strip()}")
except Exception as e:
    print(f"Error getting source: {e}")

# Check class dict directly
print("\nClass __dict__ keys:")
for key in LMStudioClient.__dict__:
    if not key.startswith('_'):
        obj = LMStudioClient.__dict__[key]
        print(f"  {key}: {type(obj).__name__}")
