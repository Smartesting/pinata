# OpenATA

Code for an LLM-powered Autonomous Testing Agent (ATA), as presented in the paper _Are Autonomous Web Agents good testers?_.

# Install

First install uv, installation details [here](https://docs.astral.sh/uv/getting-started/installation/).

1. Download dependencies

```bash
uv sync
```

2. Install playwright's chromium driver

```shell
uv run playwright install chromium
```

# Run

Execute the _run.py_ file with appropriate parameters. Example:

```bash
uv run python run.py -f test_case.json -o "./results/openai/postmill/passing" -u http://www.vtaas-benchmark.com:9980`
```

# Benchmark

To run the benchmark presented in the paper, execute the _evaluation.py_ file with the appropriate parameters:
-f : path to csv file with test cases
-o : output folder for the test case verdict, playwright trace, screenshots, and execution logs
-u : url of the application to be evaluated (default: http://www.vtaas-benchmark.com:9980)
-p : provider for the llm service (supported: "openai", "anthropic", "google", "mistral", "openrouter", default: "openai")

Examples:

Classified

`uv run python evaluation.py -f "./benchmark/classifieds_passing.csv" -o "./results/openai/postmill/passing" -u http://www.vtaas-benchmark.com:9980`

`uv run python evaluation.py -f "./benchmark/classifieds_failing.csv" -o "./results/openai/postmill/failing" -u http://www.vtaas-benchmark.com:9980`

OneStopShop

`uv run python evaluation.py -f "./benchmark/onestopshop_passing.csv" -o "./results/openai/onestopshop/passing" -u http://www.vtaas-benchmark.com:7770`

`uv run python evaluation.py -f "./benchmark/onestopshop_failing.csv" -o "./results/openai/onestopshop/failing" -u http://www.vtaas-benchmark.com:7770`

Postmill

`uv run python evaluation.py -f "./benchmark/postmill_passing.csv" -o "./results/openai/postmill/passing" -u http://www.vtaas-benchmark.com:9999`

`uv run python evaluation.py -f "./benchmark/postmill_failing.csv" -o "./results/openai/postmill/failing" -u http://www.vtaas-benchmark.com:9999`
