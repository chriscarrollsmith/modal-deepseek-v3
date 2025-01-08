# LLama 3.3 70B Inference API Hosted on Modal

## Setup

- Create a Modal account
- Install `uv` with `curl -LsSf https://astral.sh/uv/install.sh | sh` (or `wget -qO- https://astral.sh/uv/install.sh | sh`)
- Install Python with `uv python install`
- Open a terminal in this folder, then run: `uv sync`
- Authenticate with modal by running: `uv run modal token new`
- Download the Llama 3.1 model from Hugging Face with `uv run modal run download_llama.py`
- Deploy the app by running: `uv run modal deploy vllm_inference.py`
- Interact with the app by running: `uv run python client.py`

