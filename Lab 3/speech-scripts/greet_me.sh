#!/usr/bin/env bash
# AI Disclaimer: partially written with help from AI (Claude Code): the shell
# plumbing for calling the three engines and checking that the script runs
# without errors. The greeting and the comparison in the README are mine.

set -euo pipefail

VOICES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/voices"
GREETING="Hello, Yun-Chung. Your raspberry pi is awake and listening."

if [[ "${1:-}" == "--all" ]]; then
  espeak-ng -ven+f2 -k5 -s150 --stdout "$GREETING" | aplay -q
  echo "$GREETING" | festival --tts
fi

python3 -m piper \
  --model en_US-lessac-medium \
  --data-dir "$VOICES_DIR" \
  --output-raw \
  -- "$GREETING" \
  | aplay -q -r 22050 -f S16_LE -t raw -
