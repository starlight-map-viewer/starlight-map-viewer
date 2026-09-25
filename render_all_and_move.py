import os
import sys
import glob
import time
import json
import shutil
import subprocess
import logging
from logging.handlers import RotatingFileHandler
import yaml
from PIL import Image

# Taken from Starlight Repo and modified by Pickra

# ========= Options =========

# SS14 Starlight repo
STARLIGHT_REPO_DIR = "./space-station-14"

#
RENDER_OUTPUT_DIR = f'{STARLIGHT_REPO_DIR}/Resources/MapImages'

# The location to put the compiled maps in.
FINAL_MAP_DIR = './maps'

# log file
LOG_FILE = "./logs/render_log.txt"

# output viewer json?
VIEWER_JSON = True

# output parallax?
PARALLAX = False # Note: Parallax output doesn't work how it's supposed to be, It's isn't per-map parallax, it just saves default parallax at MapImages. So it's useless thing.

# ==============================

logging.basicConfig(
    handlers=[
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler(LOG_FILE, maxBytes=100000, backupCount=10)
    ],
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt='%Y-%m-%dT%H:%M:%S'
)


def log(message) -> None:
    #
    logging.debug(message)

def clean_solution() -> None:
    #
    log('Cleansing older renderer build!')

    cmd = [
        "dotnet",
        "clean",
    ]

    subprocess.run(cmd, cwd=STARLIGHT_REPO_DIR, check=True)

def build_solution() -> None:
    #
    log('Building out the renderer!')

    cmd = [
        "dotnet",
        "build",
        "Content.MapRenderer"
    ]

    subprocess.run(cmd, cwd=STARLIGHT_REPO_DIR, check=True)

def render_map(map_id: str) -> bool:
    #
    global PROJECT_BUILT

    log(f"Render map {map_id}...")

    cmd = [
        "dotnet",
        "run",
        "--no-build",
        "--project",
        "Content.MapRenderer",
        map_id
    ]

    if (VIEWER_JSON):
        cmd.append("--viewer")

    if (PARALLAX):
        cmd.append("--parallax")

    try:
        subprocess.run(cmd, cwd=STARLIGHT_REPO_DIR, check=True)
    except subprocess.CalledProcessError:
        log(f"Map rendering error {map_id}")
        return False

    return True

def get_map_list() -> list[str]:
    #
    with open(f"./{STARLIGHT_REPO_DIR}/Resources/Prototypes/_Starlight/Maps/Pools/default.yml", "r", encoding="UTF8") as f:
        return yaml.safe_load(f)[0]['maps']

def get_git_file_last_updated(map_id: str) -> int:
    #
    cmd = [
        "git",
        "log",
        "-1",
        '--format="%ct"',
        "--",
        f"./Resources/Maps/_Starlight/Stations/{map_id}.yml"
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=STARLIGHT_REPO_DIR)

    return int(result.stdout.decode('UTF-8').strip().replace('"', ''))

def main() -> None:
    #
    MANIFEST_DIR = f'{FINAL_MAP_DIR}/manifest.json'
    manifest = {}

    if os.path.exists(MANIFEST_DIR):
        with open(MANIFEST_DIR, 'r', encoding='UTF8') as f:
            # Compress and save!
            manifest = json.load(f)

    # Scrub the map output folder and the eventual home
    if os.path.exists(RENDER_OUTPUT_DIR):
        #
        shutil.rmtree(RENDER_OUTPUT_DIR)

    #
    project_built = False

    for map_id in get_map_list():
        #
        last_updated = get_git_file_last_updated(map_id[9:])
        needs_update = (map_id not in manifest
                        or '_lastChecked' not in manifest[map_id]
                        or last_updated > manifest[map_id]['_lastChecked'])

        log(f'Checking {map_id}... ' + ('Outdated, updating...' if needs_update else 'Up to date, skipping!'))

        if (needs_update):
            # Does it not exist or has been updated since last check? Then update it!
            map_file_path = f'{RENDER_OUTPUT_DIR}/{map_id}'

            # Clean and rebuild our project to ensure up-to-date stuff
            if not project_built:
                # Cleanse our solution in case shit broke
                clean_solution()

                # Building the solution so we can actually build!
                build_solution()

                project_built = True

            if render_map(map_id):
                # Move the pngs to their related folders
                map_dest_dir = os.path.join(FINAL_MAP_DIR, map_id)

                # Clean out the old
                if os.path.exists(map_dest_dir):
                    #
                    print(map_dest_dir)
                    shutil.rmtree(map_dest_dir)
                    os.makedirs(map_dest_dir, exist_ok=True)

                for file_path in glob.glob(f'{map_file_path}/*.png'):
                    #
                    img = Image.open(file_path)
                    img.save(f"{map_dest_dir}/{os.path.basename(file_path)}", optimize=True)

                # Get the json generated for the new map and add it to our manifest
                with open(f'{map_file_path}/map.json') as f:
                    #
                    manifest[map_id] = json.load(f)
                    manifest[map_id]['_lastChecked'] = int(time.time())


    with open(MANIFEST_DIR, 'w', encoding='UTF8') as f:
        # Compress and save!
        manifest['_lastChecked'] = int(time.time())

        json.dump(manifest, f, separators=(',', ':'))


if __name__ == "__main__":
    #
    main()
