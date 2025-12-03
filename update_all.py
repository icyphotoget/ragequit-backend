import subprocess
import sys


def run(cmd: list[str]):
    print(f"\n=== Running: {' '.join(cmd)} ===")
    result = subprocess.run([sys.executable] + cmd, check=False)
    if result.returncode != 0:
        print(f"[ERROR] Command failed with code {result.returncode}")


if __name__ == "__main__":
    run(["fetch_steam_data.py"])
    run(["compute_scores.py"])
    print("\n[DONE] Full update finished.")
