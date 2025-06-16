import os
import requests
from tqdm import tqdm
from pathlib import Path

def download_file(url: str, destination: str):
    """Download a file with progress bar."""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    
    with open(destination, 'wb') as file, tqdm(
        desc=os.path.basename(destination),
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as progress_bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            progress_bar.update(size)

def main():
    # Model information
    model_name = "mistral-7b-instruct-v0.1.Q4_K_M.gguf"
    model_url = "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf"
    
    # Get the cache directory
    cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")
    model_path = os.path.join(cache_dir, model_name)
    
    print(f"Downloading {model_name}...")
    print(f"This is a large file (~4GB) and may take some time to download.")
    print(f"Model will be saved to: {model_path}")
    
    try:
        download_file(model_url, model_path)
        print("\nDownload completed successfully!")
        print(f"Model saved to: {model_path}")
    except Exception as e:
        print(f"\nError downloading model: {str(e)}")
        print("\nAlternative download methods:")
        print("1. Visit: https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF")
        print("2. Download the file: mistral-7b-instruct-v0.1.Q4_K_M.gguf")
        print("3. Place it in: ~/.cache/huggingface/hub/")
        raise

if __name__ == "__main__":
    main() 