#!/bin/sh
# First-use launchers, including agy, follow installed binaries in PATH.
case ":$PATH:" in
  *:/usr/share/eitr/walker/assistants:*) ;;
  *) PATH="$PATH:/usr/share/eitr/walker/assistants"; export PATH ;;
esac
