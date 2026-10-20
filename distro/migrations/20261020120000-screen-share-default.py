"""Seed newly shipped preferences in existing homes without replacing user files."""
import subprocess

subprocess.run(['eitr-config', 'seed'], check=True)
