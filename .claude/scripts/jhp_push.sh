#!/usr/bin/env bash
set -euo pipefail
git status --short
git push origin HEAD
