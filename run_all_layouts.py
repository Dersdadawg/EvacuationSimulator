#!/usr/bin/env python3
"""
Run multiple simulations with different layouts simultaneously
"""
import subprocess
import time
from pathlib import Path

layouts = [
    ("layouts/office_correct_dimensions.json", 3, "Office Building"),
    ("layouts/hospital_complex.json", 5, "Hospital Complex"),
    ("layouts/school_building.json", 8, "School Building"),
]

print("=" * 70)
print("RUNNING ALL LAYOUTS - MULTIPLE WINDOWS")
print("=" * 70)

processes = []
for layout, agents, name in layouts:
    print(f"Starting {name}: {layout} with {agents} agents...")
    proc = subprocess.Popen(
        ["python3", "main.py", "--layout", layout, "--agents", str(agents)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    processes.append((proc, name))
    time.sleep(2)  # Stagger starts

print("\n✅ All simulations started!")
print("Close each window when done, or press Ctrl+C to stop all\n")

try:
    for proc, name in processes:
        proc.wait()
        print(f"✅ {name} completed")
except KeyboardInterrupt:
    print("\n\nStopping all simulations...")
    for proc, name in processes:
        proc.terminate()

