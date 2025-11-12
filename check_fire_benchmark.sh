#!/bin/bash
# Quick status check for fire benchmark

echo "🔥 FIRE BENCHMARK STATUS CHECK"
echo "================================"
echo ""

# Check if process is running
if ps aux | grep -v grep | grep "benchmark_with_fire.py" > /dev/null; then
    echo "✅ Status: RUNNING"
    
    # Count completed runs
    completed=$(grep -c "Completed in" benchmark_fire_output.log)
    total=60
    percent=$((completed * 100 / total))
    
    echo "📊 Progress: $completed/$total runs ($percent%)"
    echo ""
    
    # Show latest results
    echo "📋 Latest Results:"
    echo "---"
    tail -15 benchmark_fire_output.log | grep -E "Running:|Completed|Rescued:|Agent Deaths:|Max Hazard:|Success Score:"
    echo ""
    
    # Estimate time remaining
    if [ $completed -gt 0 ]; then
        avg_time=$(grep "real:" benchmark_fire_output.log | awk '{sum+=$4} END {print sum/NR}')
        remaining=$((total - completed))
        est_min=$(echo "scale=1; $remaining * $avg_time / 60" | bc)
        echo "⏱️  Estimated time remaining: ~${est_min} minutes"
    fi
else
    echo "⏹️  Status: STOPPED"
    
    # Check if completed
    if grep -q "FIRE BENCHMARK COMPLETE" benchmark_fire_output.log; then
        echo "✅ Benchmark completed!"
        echo ""
        echo "📁 Results saved to:"
        ls -lh benchmark_results/benchmark_fire_*.json 2>/dev/null | tail -1
        ls -lh benchmark_results/benchmark_fire_plots_*.png 2>/dev/null | tail -1
    else
        echo "❌ Benchmark stopped before completion"
        completed=$(grep -c "Completed in" benchmark_fire_output.log)
        echo "Completed $completed/60 runs before stopping"
    fi
fi

echo ""
echo "================================"
echo "Full log: benchmark_fire_output.log"

