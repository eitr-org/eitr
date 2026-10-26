"""Application launch argv shared by desktop Python helpers."""
from eitr_paths import code


def app_command(arguments):
    return [str(code('walker/bin/app-launch')), *arguments]
