"""Seed the shared Eitr skill for homes that already ran the Claude migration."""
import subprocess

subprocess.run(['eitr-config', 'seed'], check=True)
