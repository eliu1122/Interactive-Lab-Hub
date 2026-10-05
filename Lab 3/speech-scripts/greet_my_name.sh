#!/usr/bin/env bash
set -euo pipefail
VOICES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/voices"

python3 -m piper \
  --model en_US-lessac-medium \
  --data-dir "$VOICES_DIR" \
  --output-file welcome.wav \
  -- "Hi Hong, how are you doing?"
aplay welcome.wav