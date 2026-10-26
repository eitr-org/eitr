"""Seed the Eitr skill without replacing existing user instructions."""
import subprocess

subprocess.run(['eitr-config', 'seed'], check=True)
