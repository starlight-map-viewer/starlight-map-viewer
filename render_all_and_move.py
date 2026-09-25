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

# Taken from Starlight Repo and modified by Pickra

# ========= Options =========

# SS14 Starlight repo
STARLIGHT_REPO_DIR = "./space-station-14"

#
RENDER_OUTPUT_DIR = f'{STARLIGHT_REPO_DIR}/Resources/MapImages'

# The location to put the compiled maps in.
FINAL_MAP_DIR = './public/maps'

# log file
LOG_FILE = "./logs/render_log.txt"

# output viewer json?
VIEWER_JSON = True

# output parallax?
PARALLAX = False # Note: Parallax output doesn't work how it's supposed to be, It's isn't per-map parallax, it just saves default parallax at MapImages. So it's useless thing.

# We need to build the project?
PROJECT_BUILT = False

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


def log(message):
    logging.debug(message)

def clean_solution() -> None:
    #
    log('Cleansing older build')

    cmd = [
        "dotnet",
        "clean",
    ]

    subprocess.run(cmd, cwd=STARLIGHT_REPO_DIR, check=True)

def build_solution() -> None:
    #
    log('Cleansing older build')

    cmd = [
        "dotnet",
        "build",
        "--project",
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

    if (not PROJECT_BUILT):
        PROJECT_BUILT = True

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

def main() -> None:
    #
    manifest = {
        '_lastChecked': int(time.time()),
    }

    # Cleanse our solution in case shit broke
    clean_solution()

    # Scrub the map output folder and the eventual home
    if os.path.exists(RENDER_OUTPUT_DIR):
        #
        shutil.rmtree(RENDER_OUTPUT_DIR)

    if os.path.exists(FINAL_MAP_DIR):
        #
        shutil.rmtree(FINAL_MAP_DIR)
        os.makedirs(FINAL_MAP_DIR, exist_ok=True)

    for map_id in get_map_list():
        #
        map_file_path = f'{RENDER_OUTPUT_DIR}/{map_id}'

        if render_map(map_id):
            # Move the pngs to their related folders
            map_dest_dir = os.path.join(FINAL_MAP_DIR, map_id)
            os.makedirs(map_dest_dir, exist_ok=True)

            for file_path in glob.glob(f'{map_file_path}/*.png'):
                #
                shutil.move(file_path, map_dest_dir)

            # Get the json generated for the new map and add it to our manifest
            with open(f'{map_file_path}/map.json') as f:
                #
                manifest[map_id] = json.load(f)
                manifest[map_id]['_lastChecked'] = int(time.time())

    with open(f'{FINAL_MAP_DIR}/manifest.json', 'w', encoding='UTF8') as f:
        # Compress and save!
        json.dump(manifest, f, separators=(',', ':'))

if __name__ == "__main__":
    main()
