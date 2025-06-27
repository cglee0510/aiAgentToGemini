import os
import sys

try:
    from .__system__.index import index
except ModuleNotFoundError as e:
    print("\nModules should be imported into the project!")
    print(f"Error: {e}")
    sys.exit()

_app_ = os.path.dirname(__file__)
_obj_ = index(_app_, os.getcwd(), [])
for item in dir(_obj_):
    if item[:1] == "_":
        continue
    globals()[item] = getattr(_obj_, item)
