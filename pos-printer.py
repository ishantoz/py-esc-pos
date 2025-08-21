import os
import subprocess
import sys

def main():
    cwd = os.getcwd()
    python_path = os.path.join(cwd, ".venv", "Scripts", "python.exe")
    script_path = os.path.join(cwd, "main.py")

    if not os.path.exists(python_path):
        print(f"Error: Python not found at {python_path}")
        input("Press Enter to exit...")
        return 1
    if not os.path.exists(script_path):
        print(f"Error: Script not found at {script_path}")
        input("Press Enter to exit...")
        return 1

    # Run your main.py with the venv python
    try:
        subprocess.run([python_path, script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Script failed with exit code {e.returncode}")
        input("Press Enter to exit...")
        return e.returncode

    return 0

if __name__ == "__main__":
    sys.exit(main())
