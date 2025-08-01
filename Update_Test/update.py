import os
import requests
import subprocess
from datetime import datetime

# ------------------ CONFIG ------------------ #
GITHUB_TOKEN = "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"
REPO_OWNER = "SaikatTech"
REPO_NAME = "kloudz_product_test"  # Your repository name
BRANCH = "main"

LOCAL_FOLDER = "/home/kloudz_admin/Product/Update Test/"
LOG_FILE = "/home/kloudz_admin/Product/ota_log.log"
FILE_PATH = "Update_Test"  # Path to the file in the repo
REPO_PATH = f"repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}?ref={BRANCH}"
API_URL = f"https://api.github.com/{REPO_PATH}"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
# -------------------------------------------- #

def get_remote_file_list():
    r = requests.get(API_URL, headers=HEADERS)
    r.raise_for_status()
    return r.json()  # list of file info dicts

def get_file_names_from_github():
    return [f['name'] for f in get_remote_file_list()]

def remove_stale_local_files(remote_files):
    local_files = os.listdir(LOCAL_FOLDER)
    for file in local_files:
        if file not in remote_files:
            os.remove(os.path.join(LOCAL_FOLDER, file))
            print(f"🗑️ Deleted stale file: {file}")

def download_and_replace_all(remote_files):
    for file_info in remote_files:
        name = file_info['name']
        download_url = file_info['download_url']
        response = requests.get(download_url, headers=HEADERS)
        response.raise_for_status()
        with open(os.path.join(LOCAL_FOLDER, name), 'wb') as f:
            f.write(response.content)
        print(f"⬇️ Downloaded: {name}")

def get_local_version():
    path = os.path.join(LOCAL_FOLDER, "version.txt")
    return open(path).read().strip() if os.path.exists(path) else None

def get_remote_version(remote_files):
    for f in remote_files:
        if f['name'] == "version.txt":
            res = requests.get(f['download_url'], headers=HEADERS)
            return res.text.strip()
    return None

def run_post_install_script():
    script_path = os.path.join(LOCAL_FOLDER, "requirements.sh")
    if os.path.exists(script_path):
        os.chmod(script_path, 0o755)  # Ensure it's executable
        result = subprocess.run([script_path], shell=True, capture_output=True, text=True)
        print(f"📦 Post-install output:\n{result.stdout}")
        if result.stderr:
            print(f"⚠️ Errors during post-install:\n{result.stderr}")
    else:
        print("ℹ️ No requirements.sh found, skipping post-install.")

def log_update(version):
    with open(LOG_FILE, "a") as log:
        log.write(f"[{datetime.now()}] Updated to version {version}\n")

def perform_full_ota():
    print("🔍 Checking for updates...")
    try:
        remote_files = get_remote_file_list()
        remote_filenames = [f['name'] for f in remote_files]

        local_version = get_local_version()
        remote_version = get_remote_version(remote_files)

        print(f"📄 Local Version: {local_version}")
        print(f"📄 Remote Version: {remote_version}")

        if remote_version and remote_version != local_version:
            print("🔄 Update available. Starting OTA process...")

            # Remove outdated files
            remove_stale_local_files(remote_filenames)

            # Download all fresh files
            download_and_replace_all(remote_files)

            # Run post-install commands
            run_post_install_script()

            # Log success
            log_update(remote_version)

            print("✅ OTA Update Complete.")
        else:
            print("✅ Already up-to-date.")

    except Exception as e:
        print(f"❌ OTA Failed: {e}")

if __name__ == "__main__":
    perform_full_ota()
