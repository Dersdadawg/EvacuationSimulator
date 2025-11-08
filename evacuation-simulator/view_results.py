"""
Quick script to visualize existing simulation results
"""

import json
from src.visualize import quick_visualize

# Load the fire scenario results
print("Loading fire scenario results...")

with open('outputs/frames/fire_scenario.json', 'r') as f:
    history = json.load(f)

# Load metrics
import csv
metrics = {}
with open('outputs/metrics/fire_scenario_metrics.csv', 'r') as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    for row in reader:
        if len(row) >= 2:
            key, value = row[0], row[1]
            try:
                metrics[key] = float(value)
            except:
                metrics[key] = value

print(f"Loaded {len(history)} frames")
print(f"Metrics: {metrics}")

# Visualize
print("\nGenerating matplotlib visualization...")
print("This will show two windows:")
print("  1. Animation of the simulation")
print("  2. Metrics plots over time")
print("\nClose each window to see the next one.")

quick_visualize(history, metrics, show_animation=True, show_metrics=True)

