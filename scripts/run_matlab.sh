#!/usr/bin/env bash
# Run the analytical-fragility pipeline + figures in MATLAB (preferred) or GNU Octave (free fallback).
cd "$(dirname "$0")/.."
if command -v matlab >/dev/null 2>&1; then
  matlab -batch "run('matlab/run_analytical_fragility.m'); run('matlab/plot_analytical_results.m')"
elif command -v octave-cli >/dev/null 2>&1; then
  octave-cli --no-gui matlab/run_analytical_fragility.m
  octave-cli --no-gui --eval "graphics_toolkit('gnuplot'); run('matlab/plot_analytical_results.m')" || true
else
  echo "Neither matlab nor octave found. Open matlab/run_analytical_fragility.m in MATLAB and press Run."; exit 1
fi
