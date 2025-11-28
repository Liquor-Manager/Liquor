import sys
import requests
import zipfile
from pathlib import Path
import platform
import shutil
import json

ALLOWED_ORG = "Liquor-Manager"
PACKAGES_DIR = Path("/Liqueur_Packages") if platform.system() != "Windows" else Path("C:/Liqueur_Packages")



def add_to_packages_json(repo_name):
    packages_file = PACKAGES_DIR / "packages.json"
    if packages_file.exists():
        with open(packages_file, 'r') as f:
            packages = json.load(f)
    else:
        packages = {}

    packages[repo_name] = {"installed": True}

    with open(packages_file, 'w') as f:
        json.dump(packages, f, indent=4)

def download_package(repo_name: str, target_dir: Path) -> bool:
    try:
        api_url = f"https://api.github.com/repos/{ALLOWED_ORG}/{repo_name}"
        response = requests.get(api_url)
        response.raise_for_status()
        repo_data = response.json()

        default_branch = repo_data.get('default_branch', 'main')

        url = f"https://github.com/{ALLOWED_ORG}/{repo_name}/archive/refs/heads/{default_branch}.zip"
        response = requests.get(url, stream=True)
        response.raise_for_status()

        zip_path = target_dir / f"{repo_name}.zip"
        zip_path.parent.mkdir(parents=True, exist_ok=True)

        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)

        extracted_dir = target_dir / f"{repo_name}-{default_branch}"
        final_dir = target_dir / repo_name
        if extracted_dir.exists():
            if final_dir.exists():
                shutil.rmtree(final_dir)
            extracted_dir.rename(final_dir)

        zip_path.unlink()
        add_to_packages_json(repo_name)
        return True
    except Exception as e:
        print(f"❌ Error {e}")
        if 'zip_path' in locals() and zip_path.exists():
            zip_path.unlink()
        return False

def get_args():
    args = sys.argv[1:]
    if len(args) >= 2 and args[0] == "install":
        return {"command": "install", "package": args[1]}
    elif len(args) <= 1 and args[0] == "help":
        print("""Liqour Package - Package Manager

Using:
install <repo>                         Install Package
uninstall <repo>                       Uninstall Package
help                                   Show Help

Examples:
Liqueur install MyRepo
Liqueur install MyRepo --name MyApp
        Liqueur uninstall OldApp""")
    return {"command": None}

args = get_args()
if args["command"] == "install":
    download_package(args["package"], PACKAGES_DIR)