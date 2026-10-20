#!/bin/sh
case ":$PATH:" in
  *:/usr/share/eitr/walker/assistants:*) ;;
  *) PATH="$PATH:/usr/share/eitr/walker/assistants"; export PATH ;;
esac
