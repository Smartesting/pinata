import csv


def parse_test_cases_from_csv(file_path):
    """
    Parses the CSV file and creates a data structure of test cases.

    :param file_path: str - The file path to the CSV.
    :return: dict - A dictionary with test case names as keys and their actions and expected results as values.
    """
    test_cases = {}

    with open(file_path, mode="r", newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        current_test_case = None

        for row in reader:
            if not row or not row[0].strip():
                continue

            # Check for the test case title
            if "::" in row[1]:
                current_test_case = row[1].strip()
                test_cases[current_test_case] = {"actions": [], "expected_results": []}
            else:
                # Add actions and expected results if a test case is defined
                if current_test_case and len(row) >= 2:
                    action = row[1].strip()
                    expected_result = row[2].strip()

                    if action and action != "Actions":
                        test_cases[current_test_case]["actions"].append(action)
                    if expected_result and expected_result != "Expected Result":
                        test_cases[current_test_case]["expected_results"].append(
                            expected_result
                        )

    return test_cases
