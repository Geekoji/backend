#!/bin/bash
set -euo pipefail

# get_image_tag.sh - Retrieve or calculate the next Docker image tag version for a service
#
# Usage:
#   ./get_image_tag.sh <image-repo> [--next-version]
#
# Arguments:
#   image-repo       - Name of the Docker image repository
#                    Example: username/service-name
#
# Options:
#   --next-version - Calculate the next semantic version based on commit messages
#                    (analyzing commits until the first merge commit *after* real commits).
#
# Description:
#   By default, the script queries Docker Hub for the latest semantic version tag (X.Y.Z).
#   With --next-version flag, the script additionally analyzes recent commit messages:
#
#   Version bump detection:
#       * MAJOR (X.0.0) - commit contains "BREAKING CHANGE" or "feat!"
#       * MINOR (X.Y.0) - commit starts with "feat"
#       * PATCH (X.Y.Z) - commit starts with "fix"
#       * OTHER         - chore/docs/refactor/test/... (treated as PATCH if no higher bump found)
#
#   Merge commits act as release boundaries:
#       * Merge commits before any real commits are ignored.
#       * The first merge commit after at least one real commit stops the analysis.
#
#   If no tags are found in Docker Hub, the script starts from "0.1.0".
#
# Output:
#   Prints the current/latest tag (default) or the next semantic version (--next-version).
#
# Examples:
#   ./get_image_tag.sh username/service-name
#   → 1.4.0
#
#   ./get_image_tag.sh username/service-name --next-version
#   → 2.1.1

if [[ $# -lt 1 ]]; then
  echo "⚠️ Missing required positional argument"
  echo "Usage: ${0} <image-repo> [--next-version]"
  exit 1
fi

IMAGE_REPO=${1}
CALCULATE_NEXT=false

if [[ $# -gt 1 && ${2} == "--next-version" ]]; then
  CALCULATE_NEXT=true
fi

DOCKER_HUB_REPO_BASE_URL="https://hub.docker.com/v2/repositories"
DOCKER_HUB_SERVICE_REPO_URL="${DOCKER_HUB_REPO_BASE_URL}/${IMAGE_REPO}"

# Query Docker Hub API for tags (max 10)
response=$(curl -s "${DOCKER_HUB_SERVICE_REPO_URL}/tags?page_size=10")

# Extract latest semantic version tag (X.Y.Z)
if echo "${response}" | grep -q '"name":"[0-9]\+\.[0-9]\+\.[0-9]\+"'; then
  LATEST_VERSION=$(
    echo "${response}" |
    grep -oE '"name":"[0-9]+\.[0-9]+\.[0-9]+"' |
    sed -E 's/.*"name":"([^"]+)"/\1/' |
    sort -V |
    tail -n1
  )
else
  LATEST_VERSION=""
fi

# If no tags found → start from 0.1.0
if [[ -z "${LATEST_VERSION}" ]]; then
  echo "0.1.0"
  exit 0
fi

# If --next-version flag not set, return latest tag
if ! ${CALCULATE_NEXT}; then
  echo "${LATEST_VERSION}"
  exit 0
fi

# Parse latest version
IFS='.' read -r major minor patch <<< "${LATEST_VERSION}"

# Compare bump priority
bump_priority() {
  case ${1} in
    major) echo 3 ;;
    minor) echo 2 ;;
    patch) echo 1 ;;
    none)  echo 0 ;;
    *)     echo 0 ;;
  esac
}

max_bump="patch"
seen_regular_commit=false

# Analyze commit history
while IFS= read -r commit_hash; do
  # Count parents to detect merge commits
  num_parents=$(git log -1 --pretty=%P "${commit_hash}" | wc -w)

  if [ "${num_parents}" -ge 2 ]; then
    if ${seen_regular_commit}; then
      # Stop at the first merge **after** seeing real commits
      break
    fi
  else
    # Real commit → analyze bump
    seen_regular_commit=true
    commit_msg=$(git log -1 --pretty=format:"%s" "${commit_hash}")

    if echo "${commit_msg}" | grep -Eiq 'BREAKING CHANGE|feat!'; then
      current_bump="major"
    elif echo "${commit_msg}" | grep -Eiq '^feat'; then
      current_bump="minor"
    elif echo "${commit_msg}" | grep -Eiq '^fix'; then
      current_bump="patch"
    else
      current_bump="none"
    fi

    # Update max bump if current commit has higher priority
    if [[ $(bump_priority "${current_bump}") -gt $(bump_priority "${max_bump}") ]]; then
      max_bump="${current_bump}"
    fi
  fi
done < <(git rev-list HEAD)

# Apply bump
case ${max_bump} in
  major) NEXT_VERSION="$((major + 1)).0.0" ;;
  minor) NEXT_VERSION="${major}.$((minor + 1)).0" ;;
  patch|none) NEXT_VERSION="${major}.${minor}.$((patch + 1))" ;;
esac

echo "${NEXT_VERSION}"
