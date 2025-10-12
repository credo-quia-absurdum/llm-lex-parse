#!/bin/bash
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
echo "Cleaning up files in $SCRIPT_DIR/exp"
rm "$SCRIPT_DIR/exp"/*