Create a Modal account
Install uv
From the terminal in this folder, run: `uv sync`
Authenticate with modal by running: `uv run modal token new`
Download the Llama 3.1 model from Hugging Face with `uv run modal run download_llama.py`
Deploy the app by running: `uv run modal deploy vllm_inference.py`
Interact with the app by running: `uv run python client.py`