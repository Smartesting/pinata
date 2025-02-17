# VTaaS-recherche
La même chose mais en Python


# Run Tests with uv

The project manager uv allows using pytest without installing anything. Just run in the root folder:

``` uvx pytest ```

Since we use async calls, pytest needs pytest-asyncio, so we run the uvx with --with:

``` uvx --with pytest-asyncio pytest ```

# Run Benchmark

Create a folder to 

-f : path to csv file with TestCases
-o : output folder for the traces and results
-u : url of the application to be evaluated (default: http://www.vtaas-benchmark.com:9980)
-p : provider for the llm service (supported: "openai", "anthropic", "google", default: "openai")
Using nohup to store the logs of the execution in a file. Make sure you create the folder beforehand.

Examples:

Classified

```python src/VTAAS/benchmark/evaluation.py -f "./benchmark/classifieds_passing.csv" -o "./results/openai/postmill/passing" -u http://www.vtaas-benchmark.com:9980```

```python src/VTAAS/benchmark/evaluation.py -f "./benchmark/classifieds_failing.csv" -o "./results/openai/postmill/failing" -u http://www.vtaas-benchmark.com:9980```

OneStopShop

```python src/VTAAS/benchmark/evaluation.py -f "./benchmark/onestopshop_passing.csv" -o "./results/openai/onestopshop/passing" -u http://www.vtaas-benchmark.com:7770```

```python src/VTAAS/benchmark/evaluation.py -f "./benchmark/onestopshop_failing.csv" -o "./results/openai/onestopshop/failing" -u http://www.vtaas-benchmark.com:7770```

Postmill

```python src/VTAAS/benchmark/evaluation.py -f "./benchmark/postmill_passing.csv" -o "./results/openai/postmill/passing" -u http://www.vtaas-benchmark.com:9999```

```python src/VTAAS/benchmark/evaluation.py -f "./benchmark/postmill_failing.csv" -o "./results/openai/postmill/failing" -u http://www.vtaas-benchmark.com:9999```
