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
Using nohup to store the logs of the execution in a file. Make sure you create the folder beforehand.

Examples:

Classified (Passing) using OpenAI

```nohup python src/VTAAS/benchmark/evaluation.py \```
```-f "./data/Benchmark - Classifieds.xlsx - Passing.csv" \ ``` 
```-o "./results/openai/classifieds/passing" \ ```
```-u http://www.vtaas-benchmark.com:9980 \ ```
``` > ./results/openai/classifieds/passing/log.txt & ```

OneStopMarket (Passing) using OpenAI

```nohup python src/VTAAS/benchmark/evaluation.py \```
```-f "./data/Benchmark - OneStopMarket.xlsx - Passing" \ ```
```-o "./results/openai/onestopmarket/passing" \ ```
```-u http://www.vtaas-benchmark.com:7770 \ ```
``` > ./results/openai/onestopmarket/passing/log.txt & ```

Postmill (Passing) using OpenAI

```nohup python src/VTAAS/benchmark/evaluation.py /```
```-f "./data/Benchmark - Postmill.xlsx - Passing.csv" / ```
```-o "./results/openai/postmill/passing" / ```
```-u http://www.vtaas-benchmark.com:9999 / ```
``` > ./results/openai/postmill/passing/log.txt & ```