"""Quick diagnostic: does clicking 'Add Question' actually add question editors?"""

import asyncio, sys, subprocess


def read_file(path):
    r = subprocess.run(["cat", path], capture_output=True, text=True)
    return r.stdout


# First check if the Dash app module loads cleanly
sys.path.insert(0, "/Users/jlheller/home/Technical/repos/ai_assisted_coding/src")

import importlib, traceback as tb

for mod in ["models", "storage", "survey_maker", "survey_taker", "survey_analyzer", "app"]:
    try:
        m = importlib.import_module(mod)
        print(f"  {mod}: OK (file={getattr(m, '__file__', '?')})")
    except Exception as e:
        tb.print_exc()

print("\n=== Checking callbacks registered in app module ===")
import app as a

callbacks = getattr(a.app, "callbacks_list", [])
print(f"  Total callbacks: {len(callbacks)}")
for cb in callbacks:
    inputs = [str(i) for i in (cb.inputs or [])]
    outputs = [str(o) for o in (cb.outputs or [])]
    print(f"    inputs={inputs}")
    print(f"    outputs={outputs}")
