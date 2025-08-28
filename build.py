import PyInstaller.__main__
import escpos
import os
import sys
import shutil

# Release path
app_version = "1.0.0"
release_path = f"release/v{app_version}"
app_name = "Mohajon POS"
app_icon = "app.ico"

escpos_path = os.path.dirname(escpos.__file__)

capabilities_file = os.path.join(escpos_path, "capabilities.json")
if not os.path.exists(capabilities_file):
    capabilities_file = os.path.join(escpos_path, "resources", "capabilities.json")

if not os.path.exists(capabilities_file):
    print("ERROR: Cannot find capabilities.json in escpos package.")
    sys.exit(1)


sep = ';' if os.name == 'nt' else ':'
add_data_arg = f"{capabilities_file}{sep}escpos"

certs_data_arg = f"certs{sep}certs" if os.path.exists("certs") else ""


PyInstaller.__main__.run([
    'main.py',
    '--onefile',
    '--console',
    f'--icon={app_icon}',
    f'--name={app_name}',
    f'--distpath={release_path}',
    f'--add-data={add_data_arg}',
    f'--add-data={certs_data_arg}' if certs_data_arg else '--add-data=certs;certs',
    '--clean',
])

# Print for debug
print("Escpos package path:", escpos_path)
print("Added capabilities.json from:", capabilities_file)
if certs_data_arg:
    print("Added certs folder to PyInstaller data")
else:
    print("Warning: certs folder not found, but PyInstaller will still try to include it")

# Copy certs folder to release directory
certs_source = "certs"
certs_dest = os.path.join(release_path, "certs")

if os.path.exists(certs_source):
    if os.path.exists(certs_dest):
        shutil.rmtree(certs_dest)
    shutil.copytree(certs_source, certs_dest)
    print(f"Copied {certs_source} folder to {certs_dest}")
else:
    print(f"Warning: {certs_source} folder not found, skipping copy")
