from VTAAS.data.testcase import TestCaseCollection


class DisablePyTestCollectionMixin(object):
    __test__ = False


class TestimonialFactory(DisablePyTestCollectionMixin):
    pass


def test_collection_number():
    test_collection = TestCaseCollection("data/OneStop_Passing.csv")
    assert len(test_collection) == 29


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
