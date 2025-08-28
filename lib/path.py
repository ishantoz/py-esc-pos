import sys, os

# Helper to get the correct path for PyInstaller
def resource_path(relative_path):
    """Get absolute path to resource, works for PyInstaller --onefile"""
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
