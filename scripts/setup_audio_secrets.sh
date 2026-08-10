#!/usr/bin/env bash
set -euo pipefail
repo="${1:-$(git remote get-url origin | sed -E 's#(git@github.com:|https://github.com/)##; s#\.git$##')}"
read -r -p "Facebook-connected Instagram professional account ID: " account_id
read -r -s -p "Facebook Login user access token: " token
printf '\n'
[[ -n "$account_id" && -n "$token" ]]
printf '%s' "$account_id" | gh secret set META_AUDIO_INSTAGRAM_USER_ID -R "$repo"
printf '%s' "$token" | gh secret set META_AUDIO_ACCESS_TOKEN -R "$repo"
echo "Saved Western Reel audio credentials for $repo"
