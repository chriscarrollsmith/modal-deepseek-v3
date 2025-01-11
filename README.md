# DeepSeek v3 Inference API Hosted on Modal

This is a self-hosted DeepSeek v3 Inference API you can deploy on Modal.com. It uses [vLLM](https://vllm.ai/) to run the model.

Unfortunately, the [official bf16 DeepSeek v3 model](https://huggingface.co/cognitivecomputations/DeepSeek-V3-AWQ) requires over a terabyte of GPU memory, so it requires a larger number of H100 GPUs than Modal currently allows you to request. So instead, this repo uses an [AWQ quantized version of the model created by cognitivecomputations](https://huggingface.co/cognitivecomputations/DeepSeek-V3-AWQ), which can be run on 8 H100s. Per Claude,

> For AWQ specifically:
>
> - Quality: Usually very minor quality degradation compared to other quantization methods - often less than 1% drop in most benchmarks
> - Speed: Can be slower than FP16/BF16 because quantized operations need to be dequantized during computation
> - Memory: Major benefit - reduces memory usage by about 4x compared to BF16

## Prerequisites

- Create a [Hugging Face account](https://huggingface.co/)
- Create a [Modal account](https://modal.com/)
- Install the `uv` package manager with `curl -LsSf https://astral.sh/uv/install.sh | sh`
    - Or `wget -qO- https://astral.sh/uv/install.sh | sh` if you don't have `curl`
- Install Python with `uv python install`
- Install [git](https://git-scm.com/)

## Setup

- Clone this repo with `git clone https://github.com/chriscarrollsmith/modal-deepseek-v3.git`
- Open a terminal, `cd` into this folder, then run: `uv sync`
- Create a new `.env` file in the root of the repo with a BEARER_TOKEN to protect your API (you can use `echo "BEARER_TOKEN=$(openssl rand -hex 16)" >> .env` to generate a random value and write it to the file)
- Add this token to the [Modal secrets manager](https://modal.com/secrets/) as a secret named `api-secret` with key `BEARER_TOKEN`
- Authenticate the Modal CLI by running: `uv run modal token new`
- Download the DeepSeek V3 model from Hugging Face with `uv run modal run download_deepseek.py` (this will take a while because it's a huge model at 671B parameters)
- Deploy the app by running: `uv run modal deploy vllm_inference.py`
- Test the app by running: `uv run python client.py`