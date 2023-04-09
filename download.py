# File to download model weights during docker build:

def download_files(address):
    print("Running 'download.py'")

    import requests

    files = ["config.json", "special_tokens_map.json", "tokenizer_config.json", "tokenizer_config.json", "tokenizer.json", "training_args.bin", "pytorch_model.bin"]

    for file in files:

        url = address + file
        
        response = requests.get(url)
        print(response)

        if response.status_code == 200:
            with open(file, "wb") as f:
                f.write(response.content)
                print("Object successfully downloaded")
        else:
            print("Failed to download object")