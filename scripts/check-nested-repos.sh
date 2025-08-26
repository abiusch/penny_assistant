#!/usr/bin/env bash
set -euo pipefail

echo "::group::Nested Git repo check"

# Find any ".git" dir/file that isn't the root .git
mapfile -t offenders < <(find . -path "./.git" -prune -o -name ".git" -print | grep -vE '^./.git$' || true)

if ((${#offenders[@]})); then
  echo "Found nested Git repo markers (.git) in the tree:"
  for p in "${offenders[@]}"; do
    # Strip trailing "/.git" for readability
    echo " - ${p%/.git}"
  done
  echo "::error title=Nested repo(s) detected::Remove these nested repos or vendor them without their .git dirs."
  exit 1
else
  echo "No nested Git repos found."
fi

echo "::endgroup::"
