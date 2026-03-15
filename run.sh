#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo "Building the Docker image..."
# Use --pull to ensure we are always pulling the latest simulationcraftorg/simc:latest nightly image
docker build --pull -t tier-sims "$DIR"

if [ "$1" = "--site-only" ]; then
  echo "Generating site only..."
  # Mount generate_site.py and config.json from the host so edits don't require image rebuilds
  docker run --rm \
    -v "$DIR/docs:/app/docs" \
    -v "$DIR/config.json:/app/config.json" \
    -v "$DIR/generate_site.py:/app/generate_site.py" \
    --entrypoint python3 tier-sims -u generate_site.py
  echo "Site generated successfully! View docs/index.html to see the results."
else
  echo "Clearing old results..."
  rm -rf "$DIR/docs"
  mkdir -p "$DIR/docs"
  touch "$DIR/docs/.nojekyll"

  echo "Starting the simulation..."
  # Run the container, automatically removing it after exit (--rm)
  # Mount the local "docs" directory to "/app/docs" inside the container so we can access the generated results
  docker run --rm -v "$DIR/docs:/app/docs" tier-sims
  echo "Simulation completed successfully! You can find the results in the 'docs' directory."
fi
