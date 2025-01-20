# VTaaS-recherche
La même chose mais en Python


# Run Tests with uv

The project manager uv allows using pytest without installing anything. Just run in the root folder:

``` uvx pytest ```

Since we use async calls, pytest needs pytest-asyncio, so we run the uvx with --with:

``` uvx --with pytest-asyncio pytest ```