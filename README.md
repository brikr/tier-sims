# Tier Sims

A command-line application that uses the Simulationcraft Docker image to run simulations for World of Warcraft tier sets, comparing spec performance with and without tier set bonuses.

## Prerequisites

- **Docker** must be installed and running on your system.

## How to Run

You can build and run the entire application using the provided bash script. Open your terminal in the project's root directory and execute:

```bash
./run.sh
```

### What `run.sh` does:
1. Pulls the latest `/simc:latest` nightly image to ensure up-to-date data.
2. Builds the `tier-sims` Docker image for the project.
3. Runs the container, automatically removing it after completion.
4. Mounts the local `output` directory to save the simulation results to your machine.

## Viewing Results

Once the simulation completes successfully, you will find the generated CSV file(s) in the `output/` directory located in the same folder as the script.
