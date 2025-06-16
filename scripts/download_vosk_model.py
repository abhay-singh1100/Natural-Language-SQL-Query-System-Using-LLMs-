import os
import requests
import zipfile
from tqdm import tqdm
import shutil

def download_file(url: str, filename: str):
    """Download a file with progress bar."""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filename, 'wb') as f, tqdm(
        desc=filename,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for data in response.iter_content(chunk_size=1024):
            size = f.write(data)
            pbar.update(size)

def main():
    # Create models directory if it doesn't exist
    models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Model URL and paths
    model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    zip_path = os.path.join(models_dir, "vosk-model-small-en-us-0.15.zip")
    model_dir = os.path.join(models_dir, "vosk-model-small-en-us-0.15")
    
    # Download model if it doesn't exist
    if not os.path.exists(model_dir):
        print("Downloading Vosk model...")
        download_file(model_url, zip_path)
        
        print("Extracting model...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(models_dir)
        
        # Clean up zip file
        os.remove(zip_path)
        print("Model downloaded and extracted successfully!")
    else:
        print("Model already exists!")

if __name__ == "__main__":
    main() 