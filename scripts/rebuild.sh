#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/var/www/blog-louis/repo"
OUTPUT_DIR="/var/www/blog-louis/public"

cd "$REPO_DIR"
git pull --ff-only

hugo --minify --destination "$OUTPUT_DIR"

echo "Site herbouwd op $(date)"
