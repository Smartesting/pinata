import csv
import os
import re
from typing import override

from VTAAS.utils.logger import get_logger
from collections.abc import Sequence


logger = get_logger(__name__)


class TestCase:
    def __init__(
        self, full_name: str, actions: list[str], expected_results: list[str], url: str
    ):
        self._full_name: str = full_name
        self._parse_full_name(full_name)
        self.actions: list[str] = actions
        self.expected_results: list[str] = expected_results
        self.url: str = url
        self.steps: Sequence[tuple[str, str]] = list(
            zip(self.actions, self.expected_results)
        )

    def get_step(self, n: int) -> tuple[str, str]:
        """Get the nth step in the test case"""
        if n < 1:
            raise ValueError("Steps start at 1")
        if n > len(self.steps):
            raise ValueError(
                f"Step #{n} does not exist. Test case length: {len(self.steps)}"
            )
        return self.steps[n - 1]

    def _parse_full_name(self, full_name: str) -> None:
        """
        Parses the full name in the format "Test Case: TC-28-P :: Edit Account Information"
        to extract id, type, and name
        """
        # Extract the parts after "Test Case: TC-" and after "::"
        pattern = r"TC-(\d+)-([A-Z]) :: (.+)$"
        match = re.match(pattern, full_name)

        if match:
            self.id: str = match.group(1)
            self.type: str = match.group(2)
            self.name: str = match.group(3).strip()
        else:
            raise ValueError(f"Invalid test case format: {full_name}")

    @property
    def full_name(self) -> str:
        return f"TC-{self.id}-{self.type}: {self.name}"

    @override
    def __str__(self) -> str:
        output = self.full_name
        for idx, test_step in enumerate(self):
            output += "\n"
            output += f"{idx + 1}. {test_step[0]}"
            if test_step[1]:
                output += f"; Assertion: {test_step[0]}"
        return output

    @override
    def __repr__(self) -> str:
        return (
            f"TestCase(id='{self.id}', type='{self.type}', "
            f"name='{self.name}', actions={self.actions}, "
            f"expected_results={self.expected_results})"
        )

    # We admit there can be empty assertions, and it's ok.
    def __len__(self) -> int:
        return len(self.actions)

    def __iter__(self):
        for step in self.steps:
            yield step


class TestCaseCollection:
    # To ensure it is ignored by pytest
    __test__: bool = False

    def __init__(self, file_path: str, url: str):
        self.file_path: str = file_path
        self.name: str = self._get_file_name()
        self.url: str = url
        self.test_cases: list[TestCase] = []
        self._parse_file()
        logger.info(self)

    def _get_file_name(self) -> str:
        """
        Extracts the file name without extension from the file path
        """
        return os.path.splitext(os.path.basename(self.file_path))[0]

    def _parse_file(self) -> None:
        """
        Parses the file and creates TestCase instances.
        Currently supports CSV files only.
        """
        if not self.file_path.lower().endswith(".csv"):
            raise ValueError("Currently only CSV files are supported")

        test_cases_dict = self._parse_csv()
        self._create_test_cases(test_cases_dict)

    def _parse_csv(self) -> dict[str, dict[str, list[str]]]:
        """
        Parses the CSV file and returns a dictionary of test cases.
        """
        test_cases: dict[str, dict[str, list[str]]] = {}

        with open(self.file_path, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            current_test_case = None

            for row in reader:
                if not row or not row[0].strip():
                    continue

                # Check for the test case title
                if "::" in row[1]:
                    current_test_case = row[1].strip()
                    test_cases[current_test_case] = {
                        "actions": [],
                        "expected_results": [],
                    }
                else:
                    # Add actions and expected results if a test case is defined
                    if current_test_case and len(row) >= 2:
                        action = row[1].strip() if len(row) > 1 else ""
                        expected_result = row[2].strip() if len(row) > 2 else ""

                        if action != "Actions":
                            test_cases[current_test_case]["actions"].append(action)
                        if expected_result != "Expected Result":
                            test_cases[current_test_case]["expected_results"].append(
                                expected_result
                            )

        return test_cases

    def _create_test_cases(
        self, test_cases_dict: dict[str, dict[str, list[str]]]
    ) -> None:
        """
        Creates TestCase instances from the parsed dictionary.
        """
        for full_name, data in test_cases_dict.items():
            test_case = TestCase(
                full_name=full_name,
                actions=data["actions"],
                expected_results=data["expected_results"],
                url=self.url,
            )
            self.test_cases.append(test_case)

    def get_test_case_by_id(self, id: str) -> TestCase:
        """
        Returns a test case by its ID.
        """
        for test_case in self.test_cases:
            if test_case.id == id:
                return test_case
        raise ValueError(f"No test case found with ID: {id}")

    def get_test_cases_by_type(self, type: str) -> list[TestCase]:
        """
        Returns all test cases of a specific type.
        """
        return [tc for tc in self.test_cases if tc.type == type]

    def get_test_case_by_name(self, name: str) -> TestCase:
        """
        Returns a test case by its name.
        """
        for test_case in self.test_cases:
            if test_case.name == name:
                return test_case
        raise ValueError(f"No test case found with name: {name}")

    def __iter__(self):
        return iter(self.test_cases)

    def __len__(self):
        return len(self.test_cases)

    @override
    def __str__(self) -> str:
        return f"TestCaseCollection: {self.name} ({len(self)} test cases)"
