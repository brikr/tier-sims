# Tier Sims

A command-line application that uses the SimulationCraft Docker image to run sims for World of Warcraft tier sets, comparing spec performance with and without tier set bonuses.

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

## Configuration

The application is configured via `config.json`. Below are the available fields:

- **`branch`**: The git branch of the SimulationCraft repository to pull profiles from (e.g., `"midnight"`).
- **`season_dir`**: The directory within `profiles/` on GitHub (e.g., `"MID1"`).
- **`tier_set_name`**: The internal SimC name for the tier set bonuses (e.g., `"midnight_season_1"`).
- **`profile`** *(optional)*: The specific filename of a `.simc` profile to run. If omitted, the script will attempt to run all profiles found in the `season_dir`.

Example `config.json`:

```json
{
  "branch": "midnight",
  "season_dir": "MID1",
  "tier_set_name": "midnight_season_1",
  "profile": "MID1_Demon_Hunter_Devourer"
}
```

## Viewing Results

Once the simulation completes successfully, you will find a summary of the sims in `output/tier_sims.csv`. For each sim ran, the simc HTML output is saved to `output/{spec_name}.html`.
