from VTAAS.data.testcase import TestCaseCollection  # type: ignore


class DisablePyTestCollectionMixin(object):
    __test__ = False


class TestimonialFactory(DisablePyTestCollectionMixin):
    pass


def test_collection_number():
    test_collection = TestCaseCollection("data/OneStop_Passing.csv")
    assert len(test_collection) == 31


def test_TC_id_getter():
    test_collection = TestCaseCollection("data/OneStop_Passing.csv")

    # Get test cases in different ways
    specific_test = test_collection.get_test_case_by_id("28")
    assert specific_test.name == "Edit Account Information"


def test_TC_name_getter():
    test_collection = TestCaseCollection("data/OneStop_Passing.csv")

    name_test = test_collection.get_test_case_by_name(
        "Product Selection and Cart Verification"
    )
    assert int(name_test.id) == 3


def test_action_assertion_numbers():
    test_collection = TestCaseCollection("data/OneStop_Passing.csv")

    name_test = test_collection.get_test_case_by_name(
        "Product Selection and Cart Verification"
    )

    assert len(name_test.actions) == len(name_test.expected_results)

    # test with empty action
    name_test = test_collection.get_test_case_by_name("test_empty_action")
    print(name_test.actions)
    assert len(name_test.actions) == len(name_test.expected_results)

    # test with empty assertion
    name_test = test_collection.get_test_case_by_name("test_empty_assertion")
    assert len(name_test.actions) == len(name_test.expected_results)


def test_steps_generator():
    test_collection = TestCaseCollection("data/OneStop_Passing.csv")

    name_test = test_collection.get_test_case_by_name(
        "Product Selection and Cart Verification"
    )
    i = 0
    for _ in name_test:
        i += 1

    assert i == 7
