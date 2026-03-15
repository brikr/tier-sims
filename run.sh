#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Building the Docker image..."
# Use --pull to ensure we are always pulling the latest simulationcraftorg/simc:latest nightly image
docker build --pull -t tier-sims .

echo "Starting the simulation..."
# Run the container, automatically removing it after exit (--rm)
# Mount the local "output" directory to "/app/output" inside the container so we can access the generated CSV
docker run --rm -v "$(pwd)/output:/app/output" tier-sims

echo "Simulation completed successfully! You can find the results in the 'output' directory."
