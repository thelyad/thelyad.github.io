#!/usr/bin/env bash
set -euo pipefail

# Build posts: compile Markdown in posts/md to HTML in posts/html
# and regenerate posts/index.html. No external packages required.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "$SCRIPT_DIR/generate_posts_index.py"

echo "Done. Open posts/index.html to view the list."

