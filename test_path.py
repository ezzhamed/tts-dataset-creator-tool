import os
import sys

file_path = "/app/backend/worker.py"
root_triple = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(file_path))))
root_double = os.path.dirname(os.path.dirname(os.path.abspath(file_path)))

print(f"Triple: {root_triple}")
print(f"Double: {root_double}")
