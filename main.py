import os
import json
import csv
import subprocess
import requests
import re

CONFIG_FILE = "config.json"
OUTPUT_DIR = "docs"

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def get_simc_files(branch, season_dir):
    """Fetches the list of .simc files from the GitHub API."""
    url = f"https://api.github.com/repos/simulationcraft/simc/contents/profiles/{season_dir}?ref={branch}"
    response = requests.get(url)
    response.raise_for_status()
    all_files = response.json()

    simc_files = {}
    for file_info in all_files:
        name = file_info["name"]
        if name.endswith(".simc"):
            simc_files[name] = file_info["download_url"]

    return simc_files

def process_profile(name, download_url, tier_set_name, spec_name):
    """Downloads a profile, injects tier overrides, runs SimC, and parses the output JSON and HTML."""
    print(f"Processing {name}...")
    response = requests.get(download_url)
    response.raise_for_status()
    content = response.text

    # 1. Change the base character name to "4p"
    # Find the very first line which is usually class="name" e.g., warlock="DF2_Warlock_Affliction"
    lines = content.splitlines()
    if lines:
        first_line = lines[0]
        # Regex to replace the value inside the quotes with "4p"
        lines[0] = re.sub(r'="[^"]+"', '="4p"', first_line)

    # 2. Append profilesets for 0p and 2p
    profileset_lines = [
        "",
        f'profileset."0p"+=set_bonus={tier_set_name}_2pc=0/{tier_set_name}_4pc=0',
        "",
        f'profileset."2p"+=set_bonus={tier_set_name}_2pc=1/{tier_set_name}_4pc=0',
    ]

    custom_content = "\n".join(lines + profileset_lines)

    temp_simc = "temp.simc"
    temp_json = "temp.json"

    with open(temp_simc, "w") as f:
        f.write(custom_content)

    # 3. Run simc
    # We assume 'simc' is available in PATH (as it should be in the docker container)
    html_path = os.path.join(OUTPUT_DIR, f"{spec_name}.html")
    try:
        # Run simc, outputting to temp.json and HTML
        subprocess.run(["/app/SimulationCraft/simc", temp_simc, f"json2={temp_json}", f"html={html_path}"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running simc for {name}: {e}")
        # Optional: you can debug the stderr if it fails, but we'll return None for now
        return None

    # 4. Parse JSON
    if not os.path.exists(temp_json):
        print(f"No JSON output found for {name}")
        return None

    with open(temp_json, "r") as f:
        data = json.load(f)

    results = {"0p": 0, "2p": 0, "4p": 0}

    # simc json2 format has 'sim' -> 'players' as an array
    if "sim" in data and "players" in data["sim"]:
        for player in data["sim"]["players"]:
            p_name = player.get("name")
            dps = player.get("collected_data", {}).get("dps", {}).get("mean", 0)
            if p_name in results:
                results[p_name] = round(dps)

    if "sim" in data and "profilesets" in data["sim"] and "results" in data["sim"]["profilesets"]:
        for pset in data["sim"]["profilesets"]["results"]:
            pset_name = pset.get("name")
            dps = pset.get("mean", 0)
            if pset_name in results:
                results[pset_name] = round(dps)

    # 5. Save build info from the first sim
    build_info_path = os.path.join(OUTPUT_DIR, "build_info.json")
    if not os.path.exists(build_info_path):
        build_info = {}
        if "build_date" in data:
            build_info["build_date"] = data["build_date"]
        if "build_time" in data:
            build_info["build_time"] = data["build_time"]
        if "git_revision" in data:
            build_info["git_revision"] = data["git_revision"]
        if build_info:
            with open(build_info_path, "w") as f:
                json.dump(build_info, f, indent=2)
            print(f"Saved build info to {build_info_path}")

    if os.path.exists(temp_simc):
        os.remove(temp_simc)
    if os.path.exists(temp_json):
        os.remove(temp_json)

    return results

def main():
    config = load_config()
    branch = config["branch"]
    season_dir = config["season_dir"]
    tier_set_name = config["tier_set_name"]
    target_profile = config.get("profile")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    specs = get_simc_files(branch, season_dir)

    if target_profile:
        if not target_profile.endswith(".simc"):
            target_profile += ".simc"
        if target_profile in specs:
            specs = {target_profile: specs[target_profile]}
        else:
            print(f"Profile '{target_profile}' not found in '{season_dir}'.")
            return

    print(f"Found {len(specs)} profiles to simulate in '{season_dir}' via branch '{branch}'.")

    csv_filename = os.path.join(OUTPUT_DIR, "tier_sims.csv")
    with open(csv_filename, "w", newline="") as csvfile:
        fieldnames = ["Spec", "0p", "2p", "4p", "0p to 2p", "2p to 4p", "0p to 4p"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for name, url in specs.items():
            spec_name = name.replace(".simc", "")
            results = process_profile(name, url, tier_set_name, spec_name)
            if results:
                diff_0_to_2 = results["2p"] - results["0p"]
                diff_2_to_4 = results["4p"] - results["2p"]
                diff_0_to_4 = results["4p"] - results["0p"]
                writer.writerow({
                    "Spec": spec_name,
                    "0p": results["0p"],
                    "2p": results["2p"],
                    "4p": results["4p"],
                    "0p to 2p": diff_0_to_2,
                    "2p to 4p": diff_2_to_4,
                    "0p to 4p": diff_0_to_4,
                })
                # Flush to ensure output is written incrementally in case of interruption
                csvfile.flush()
                print(f"Finished {spec_name}: 0p={results['0p']}, 2p={results['2p']}, 4p={results['4p']}")
            else:
                print(f"Failed to process {spec_name}")

    print(f"Successfully generated {csv_filename}")

if __name__ == "__main__":
    main()
