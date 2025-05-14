#!/bin/sh

# Default transport to stdio
TRANSPORT_MODE="stdio"

# Check if DROIDMIND_TRANSPORT is set and not empty
if [ -n "$DROIDMIND_TRANSPORT" ]; then
  TRANSPORT_MODE="$DROIDMIND_TRANSPORT"
fi

# If CMD is just 'droidmind' or empty, use default args for the chosen transport
if [ "$#" -eq 0 ] || { [ "$#" -eq 1 ] && [ "$1" = "droidmind" ]; }; then
  if [ "$TRANSPORT_MODE" = "sse" ]; then
    exec droidmind --transport sse --host 0.0.0.0 --port 4256
  else
    exec droidmind --transport stdio
  fi
else
  # If CMD has other arguments, pass them through, but ensure --transport is set correctly
  # This is a bit more complex to do perfectly without overriding user's explicit --transport
  # For now, we'll prioritize DROIDMIND_TRANSPORT if no --transport is in CMD args
  HAS_TRANSPORT_ARG=false

  # Loop through arguments to check for --transport flag
  for arg in "$@"; do
    if [ "$arg" = "--transport" ]; then
      HAS_TRANSPORT_ARG=true
      break
    fi
  done

  if [ "$HAS_TRANSPORT_ARG" = "false" ]; then
    exec droidmind --transport "$TRANSPORT_MODE" "$@"
  else
    # User has provided --transport, let it be
    exec droidmind "$@"
  fi
fi
