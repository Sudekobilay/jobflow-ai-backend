#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF
Usage: $0 <repository>[:tag]
Example: $0 myuser/jobflow-ai-backend:latest
If tag is omitted, 'latest' will be used.
EOF
}

if [ "$#" -ne 1 ]; then
  usage
  exit 1
fi

REPO_TAG="$1"
if [[ "$REPO_TAG" != *":"* ]]; then
  REPO_TAG="$REPO_TAG:latest"
fi

echo "Building image $REPO_TAG"
docker build -t "$REPO_TAG" .

echo "Pushing image $REPO_TAG"
docker push "$REPO_TAG"

echo "Done."
