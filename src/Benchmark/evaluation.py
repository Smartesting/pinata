from VTAAS.data.testcase import TestCaseCollection
from VTAAS.orchestrator.orchestrator import Orchestrator
from VTAAS.schemas.verdict import Status


async def run_evaluation(tc_collection: TestCaseCollection) -> dict[str, float]:
    metrics: dict[str, float] = {}

    metrics["FN"] = 0
    metrics["TN"] = 0
    metrics["FP"] = 0
    metrics["AFA"] = 0
    metrics["AFB"] = 0
    metrics["AFC"] = 0

    for test_case in tc_collection:
        orchestrator = Orchestrator()

        execution_result = await orchestrator.process_testcase(test_case)

        if execution_result.status == Status.PASS:
            if test_case.type == "F":
                metrics["FN"] = metrics["FN"] + 1
            elif test_case.type == "P":
                print("TN")

        else:
            if test_case.type == "F":
                match execution_result.step_index:
                    case _ if execution_result.step_index < test_case.failing_step:
                        metrics["AFB"] = metrics["AFB"] + 1
                    case _ if execution_result.step_index == test_case.failing_step:
                        metrics["AFC"] = metrics["AFC"] + 1
                    case _ if execution_result.step_index > test_case.failing_step:
                        metrics["AFA"] = metrics["AFA"] + 1

            elif test_case.type == "P":
                metrics["FP"] = metrics["FP"] + 1

    metrics["TP"] = metrics["AFA"] + metrics["AFB"] + metrics["AFC"]
    metrics["accuracy"] = (metrics["TP"] + metrics["TN"]) / (
        metrics["TP"] + metrics["TN"] + metrics["FP"] + metrics["FN"]
    )
    metrics["specificity"] = metrics["TN"] / (metrics["TN"] + metrics["FP"])
    metrics["sensitivity"] = metrics["TP"] / (metrics["TP"] + metrics["FN"])
    metrics["AER"] = metrics["AFB"] / metrics["TP"]
    metrics["HER"] = metrics["AFA"] / metrics["TP"]
    metrics["SMER"] = metrics["AER"] + metrics["HER"]
    metrics["truacc"] = (metrics["AFC"] + metrics["TN"]) / (
        metrics["TP"] + metrics["TN"] + metrics["FP"] + metrics["FN"]
    )

    return metrics
