@ECHO OFF

if not exist "space-station-14" (
    ECHO No Starlight repo found. Fetching it!
    git clone https://github.com/ss14Starlight/space-station-14.git
    python3 ./space-station-14/RUN_THIS.py
) else (
    ECHO Running a quick update on the Starlight repo.
    git -C ./space-station-14 pull
)

REM Do our renders and move them!
%CD%/.venv/Scripts/python render_all_and_move.py
