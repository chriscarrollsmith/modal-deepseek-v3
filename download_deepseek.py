# ---
# args: ["--force-download"]
# ---

import modal

MODELS_DIR = "/deepseeks"

DEFAULT_NAME = "cognitivecomputations/DeepSeek-V3-AWQ"
DEFAULT_REVISION = "604068d51215c8778b3ae1223ff5686f6c9e7729"

volume = modal.Volume.from_name("deepseeks", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        [
            "huggingface_hub",  # download models from the Hugging Face Hub
            "hf-transfer",  # download models faster with Rust
        ]
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)


MINUTES = 60
HOURS = 60 * MINUTES


app = modal.App(
    image=image,
    # secrets=[  # add a Hugging Face Secret if you need to download a gated model
    #     modal.Secret.from_name("huggingface-secret", required_keys=["HF_TOKEN"])
    # ]
)


@app.function(volumes={MODELS_DIR: volume}, timeout=4 * HOURS)
def download_model(model_name, model_revision, force_download=False):
    from huggingface_hub import snapshot_download

    volume.reload()

    snapshot_download(
        model_name,
        local_dir=MODELS_DIR + "/" + model_name,
        ignore_patterns=[
            "*.pt",
            "*.bin",
            "*.pth",
            "original/*",
        ],  # Ensure safetensors
        revision=model_revision,
        force_download=force_download,
    )

    volume.commit()


@app.local_entrypoint()
def main(
    model_name: str = DEFAULT_NAME,
    model_revision: str = DEFAULT_REVISION,
    force_download: bool = False,
):
    download_model.remote(model_name, model_revision, force_download)
