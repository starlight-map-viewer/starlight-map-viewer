import time
import subprocess

def git_add() -> bool:
    cmd = [
        "git",
        "add",
        ".",
    ]

    try:
        #
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        #
        return False

    return True

def git_commit() -> bool:
    cmd = [
        "git",
        "commit",
        "-m",
        '"Automated commit to update maps"'
    ]

    try:
        #
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        #
        return False

    return True

def git_push() -> bool:
    cmd = [
        "git",
        "push",
    ]

    try:
        #
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        #
        return False

    return True

def are_changes_pending() -> bool:
    cmd = [
        "git",
        "status",
        "--porcelain",
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return len(result.stdout.decode('UTF8').split('\n')) > 0

def main() -> None:
    #
    if are_changes_pending() and git_add() and git_commit():
        git_push()

if __name__ == '__main__':
    main()