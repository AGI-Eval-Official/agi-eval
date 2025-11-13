import os
import requests
import subprocess
import tarfile
from agieval.common.logger import log, log_error

DATASET_CONFIG_FILE = "config.py"
DATASET_PATH = "example/dataset"
DATASETS_FILE = "datasets.txt"
DATASETS_FILE_PACKAGE = "files.tar.gz"
DATASET_GITURL = "https://raw.githubusercontent.com/AGI-Eval-Official/agi-eval-benchmarks/master"
DATASET_TEMP_DIR = "/tmp/agieval_dataset/"

def get_datasets():
    datasets = get_datasets_from_git()
    for dir in os.listdir(DATASET_PATH):
        config_file = os.path.join(DATASET_PATH, dir, DATASET_CONFIG_FILE)
        if os.path.exists(config_file) and dir not in datasets:
            datasets.append(dir)
    return datasets


def get_datasets_from_git():
    try:
        content = download_file(f"{DATASET_GITURL}/{DATASETS_FILE}")
        return [dataset.strip() for dataset in content.split("\n")]
    except Exception as e:
        log_error(f"get the adapted datasets error: {str(e)}")
        return []

def download_dataset_config(dataset, dataset_config_path):
    config_path  = os.path.dirname(dataset_config_path)
    os.makedirs(config_path, exist_ok=True)
    if os.path.exists(dataset_config_path):
        msg = f"Dataset {dataset} configuration file {dataset_config_path} already exists, will not download again"
        log(msg)
        print(msg)
        return
    try:
        download_file(f"{DATASET_GITURL}/{dataset}/{DATASET_CONFIG_FILE}", dataset_config_path)
    except Exception as e:
        msg = f"download dataset {dataset} config error: {str(e)}"
        log_error(msg)
        print(msg)
        return []


def download_dataset_from_git(dataset, dataset_dir):
    os.makedirs(dataset_dir, exist_ok=True)
    if os.path.exists(dataset_dir) and os.path.isdir(dataset_dir):
        # Check if directory is empty
        if any(os.scandir(dataset_dir)):
            log(f"Dataset {dataset} already exists, will not download again")
            return True
    
    # If dataset doesn't exist or is empty, download it
    log(f"Dataset {dataset} does not exist, starting download...")

    try:
        download_dataset_files(dataset, dataset_dir)
    except Exception as e:
        log_error(f"Unknown error occurred while downloading dataset {dataset}: {str(e)}")
        # If download fails, delete possibly created empty directory
        if os.path.exists(dataset_dir) and not any(os.scandir(dataset_dir)):
            try:
                os.rmdir(dataset_dir)
            except Exception as e:
                log_error(f"Error deleting empty directory: {str(e)}")
        return False
    log(f"Dataset {dataset} downloaded successfully")
    return True



def download_file(url, save_path = ""): 
    response = requests.get(url)
    response.raise_for_status()
    content = response.content.decode('utf-8')

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'w') as f:
            f.write(content)
    return content
        
def download_dataset_files(dataset, output_dir):
    output_file = f"{dataset}.tar.gz"
    os.makedirs(DATASET_TEMP_DIR, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    url = f"{DATASET_GITURL}/{dataset}/{DATASETS_FILE_PACKAGE}"
    
    archive_path = os.path.join(DATASET_TEMP_DIR, output_file)
    
    try:
        process = subprocess.Popen([
            "curl", "-L", url,
            "--progress-bar",
            "-o", archive_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        while True:
            output = process.stderr.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                progress_line = output.strip()
                if progress_line:
                    log(f"Download progress: {progress_line}")

        return_code = process.poll()
        if return_code != 0:
            stdout, stderr = process.communicate()
            raise subprocess.CalledProcessError(return_code, process.args, stdout, stderr)

        with tarfile.open(archive_path, 'r:*') as tar:
            tar.extractall(output_dir)
    finally:
        os.remove(archive_path)