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

# Tests

To run the unit test cases:

```shell
uv run pytest -m "not llm"
```

If you want to run a single file:

```shell
uv run pytest ./tests/test_actor.py -m "not llm"
```

The -m flag allows you to filter out certain test cases based on their mark.
We have marked as "llm" the test cases that involve a actual LLM call.
LLM test cases are integration/system test cases, we deliberately ignore them when running unit tests.
To run them:

```shell
uv run pytest ./tests/test_actor.py -ms "llm"
```

For integration tests we use the -s flag that prints output in real time and regardless of the test case outcome.

# Run

Execute the _run.py_ file with the appropriate parameters:

- -f: path to JSON file containing the test case
- -p: provider for the llm service (supported: "openai", "anthropic", "google", "mistral", "openrouter", default: "openai")

Example:

```bash
uv run python run.py -f test_case.json -p google
```

The expected JSON format for a test case is as follows:

```json
{
  "name": "test case name",
  "url": "website url"
  "actions": [
    {
      "action": "action 1",
      "expectedResult": "assertion 1"
    },
    {
      "action": "action 2",
      "expectedResult": "assertion 2"
    },
  ]
}
```

# Benchmark

To run the benchmark presented in the paper, execute the _evaluation.py_ file with the appropriate parameters:

- -f: path to csv file with test cases
- -o: output folder for the test case verdict, playwright trace, screenshots, and execution logs
- -u: url of the application to be evaluated (default: http://www.vtaas-benchmark.com:9980)
- -p: provider for the llm service (supported: "openai", "anthropic", "google", "mistral", "openrouter", default: "openai")

### Classified

`uv run python evaluation.py -f "./benchmark/classifieds_passing.csv" -o "./results/openai/classifieds/passing" -u http://www.vtaas-benchmark.com:9980`

`uv run python evaluation.py -f "./benchmark/classifieds_failing.csv" -o "./results/openai/classifieds/failing" -u http://www.vtaas-benchmark.com:9980`

### OneStopShop

`uv run python evaluation.py -f "./benchmark/onestopshop_passing.csv" -o "./results/openai/onestopshop/passing" -u http://www.vtaas-benchmark.com:7770`

`uv run python evaluation.py -f "./benchmark/onestopshop_failing.csv" -o "./results/openai/onestopshop/failing" -u http://www.vtaas-benchmark.com:7770`

### Postmill

`uv run python evaluation.py -f "./benchmark/postmill_passing.csv" -o "./results/openai/postmill/passing" -u http://www.vtaas-benchmark.com:9999`

`uv run python evaluation.py -f "./benchmark/postmill_failing.csv" -o "./results/openai/postmill/failing" -u http://www.vtaas-benchmark.com:9999`
