import modal

# Create a Modal container with Debian 12, Python 3.12, vLLM, and FastAPI
vllm_image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "vllm==0.6.6post1", "fastapi[standard]==0.115.6"
)

# Download the model weights for DeepSeek V3 to a Modal Volume
MODELS_DIR = "/deepseeks"
MODEL_NAME = "cognitivecomputations/DeepSeek-V3-AWQ"
MODEL_REVISION = "604068d51215c8778b3ae1223ff5686f6c9e7729"

try:
    volume = modal.Volume.lookup("deepseeks", create_if_missing=False)
except modal.exception.NotFoundError:
    raise Exception("Download models first with modal run download_deepseek.py")


# Build a vLLM engine and serve it as a FastAPI app
app = modal.App(
    "example-vllm-openai-compatible",
    secrets=[
        modal.Secret.from_name("api-secret", required_keys=["BEARER_TOKEN"])
    ]
)

# Set the number of GPUs to use
N_GPU = 8  # max 8

# Set the timeout for the container
MINUTES = 60  # seconds
HOURS = 60 * MINUTES

@app.function(
    image=vllm_image,
    gpu=[modal.gpu.H100(count=N_GPU)],
    container_idle_timeout=5 * MINUTES,
    timeout=24 * HOURS,
    allow_concurrent_inputs=1000,
    volumes={MODELS_DIR: volume},
)
@modal.asgi_app()
def serve():
    import os
    import fastapi
    import vllm.entrypoints.openai.api_server as api_server
    from vllm.engine.arg_utils import AsyncEngineArgs
    from vllm.engine.async_llm_engine import AsyncLLMEngine
    from vllm.entrypoints.logger import RequestLogger
    from vllm.entrypoints.openai.serving_chat import OpenAIServingChat
    from vllm.entrypoints.openai.serving_completion import (
        OpenAIServingCompletion,
    )
    from vllm.entrypoints.openai.serving_engine import BaseModelPath
    from vllm.usage.usage_lib import UsageContext

    volume.reload()  # ensure we have the latest version of the weights

    # create a fastAPI app that uses vLLM's OpenAI-compatible router
    web_app = fastapi.FastAPI(
        title=f"OpenAI-compatible {MODEL_NAME} server",
        description="Run an OpenAI-compatible LLM server with vLLM on modal.com 🚀",
        version="0.0.1",
        docs_url="/docs",
    )

    # security: CORS middleware for external requests
    http_bearer = fastapi.security.HTTPBearer(
        scheme_name="Bearer Token",
        description="See code for authentication details.",
    )
    web_app.add_middleware(
        fastapi.middleware.cors.CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # security: inject dependency on authed routes
    async def is_authenticated(api_key: str = fastapi.Security(http_bearer)):
        if api_key.credentials != os.environ["BEARER_TOKEN"]:
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return {"username": "authenticated_user"}

    router = fastapi.APIRouter(dependencies=[fastapi.Depends(is_authenticated)])

    # wrap vllm's router in auth router
    router.include_router(api_server.router)
    # add authed vllm to our fastAPI app
    web_app.include_router(router)

    engine_args = AsyncEngineArgs(
        model=MODELS_DIR + "/" + MODEL_NAME,
        tensor_parallel_size=N_GPU,
        gpu_memory_utilization=0.90,
        max_model_len=4096,
        enforce_eager=False,  # capture the graph for faster inference, but slower cold starts (30s > 20s)
        trust_remote_code=True,
    )

    engine = AsyncLLMEngine.from_engine_args(
        engine_args, usage_context=UsageContext.OPENAI_API_SERVER
    )

    model_config = get_model_config(engine)

    request_logger = RequestLogger(max_log_len=2048)

    base_model_paths = [
        BaseModelPath(name=MODEL_NAME.split("/")[1], model_path=MODEL_NAME)
    ]

    api_server.chat = lambda s: OpenAIServingChat(
        engine,
        model_config=model_config,
        base_model_paths=base_model_paths,
        chat_template=None,
        response_role="assistant",
        lora_modules=[],
        prompt_adapters=[],
        request_logger=request_logger,
    )
    api_server.completion = lambda s: OpenAIServingCompletion(
        engine,
        model_config=model_config,
        base_model_paths=base_model_paths,
        lora_modules=[],
        prompt_adapters=[],
        request_logger=request_logger,
    )

    return web_app


# Get the model config
def get_model_config(engine):
    import asyncio

    try:  # adapted from vLLM source -- https://github.com/vllm-project/vllm/blob/507ef787d85dec24490069ffceacbd6b161f4f72/vllm/entrypoints/openai/api_server.py#L235C1-L247C1
        event_loop = asyncio.get_running_loop()
    except RuntimeError:
        event_loop = None

    if event_loop is not None and event_loop.is_running():
        # If the current is instanced by Ray Serve,
        # there is already a running event loop
        model_config = event_loop.run_until_complete(engine.get_model_config())
    else:
        # When using single vLLM without engine_use_ray
        model_config = asyncio.run(engine.get_model_config())

    return model_config
