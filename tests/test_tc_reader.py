from VTAAS.utils.test_case_reader import parse_test_cases_from_csv


def test_TC_reader():
    test_cases = parse_test_cases_from_csv("data/OneStop_Passing.csv")

    for case, data in test_cases.items():
        print(f"Test Case: {case}")
        # print("Actions:")
        # for action in data["actions"]:
        #     print(f"- {action}")
        # print("Expected Results:")
        # for result in data["expected_results"]:
        #     print(f"- {result}")
