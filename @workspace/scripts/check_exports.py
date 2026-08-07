import sys
sys.path.insert(0, 'd:/Sanskriti_AI_Studio')

import importlib.util

# Check coder_agent
spec = importlib.util.spec_from_file_location('coder_agent', 'd:/Sanskriti_AI_Studio/ai_agents/scripts/coder_agent.py')
if spec is None:
    raise ImportError(f"Failed to load coder_agent.py - spec is None")

loader = getattr(spec, 'loader', None)
if loader is None:
    raise ImportError(f"Failed to load coder_agent.py - spec has no loader")
    
coder_agent = importlib.util.module_from_spec(spec)
loader.exec_module(coder_agent)
print("Coder Agent exports:", [x for x in dir(coder_agent) if not x.startswith('_')])

# Check tester_agent
spec2 = importlib.util.spec_from_file_location('tester_agent', 'd:/Sanskriti_AI_Studio/ai_agents/scripts/tester_agent.py')
if spec2 is None:
    raise ImportError(f"Failed to load tester_agent.py - spec is None")

loader2 = getattr(spec2, 'loader', None)
if loader2 is None:
    raise ImportError(f"Failed to load tester_agent.py - spec has no loader")
    
tester_agent = importlib.util.module_from_spec(spec2)
loader2.exec_module(tester_agent)
print("Tester Agent exports:", [x for x in dir(tester_agent) if not x.startswith('_')])

# Check reviewer_agent
spec3 = importlib.util.spec_from_file_location('reviewer_agent', 'd:/Sanskriti_AI_Studio/ai_agents/scripts/reviewer_agent.py')
if spec3 is None:
    raise ImportError(f"Failed to load reviewer_agent.py - spec is None")

loader3 = getattr(spec3, 'loader', None)
if loader3 is None:
    raise ImportError(f"Failed to load reviewer_agent.py - spec has no loader")
    
reviewer_agent = importlib.util.module_from_spec(spec3)
loader3.exec_module(reviewer_agent)
print("Reviewer Agent exports:", [x for x in dir(reviewer_agent) if not x.startswith('_')])
