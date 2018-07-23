""" Helper Methods for Journal Tests and Test Data """
from .factories import JournalAboutPageFactory, JournalPageFactory

# Default test data for a journal
TEST_JOURNAL_STRUCTURE = {
            "title": "test_journal_about_page",
            "structure": [
                {
                    "title": "test_page_1",
                    "children": [
                        {
                            "title": "test_page_1_a",
                            "children": [
                                {
                                    "title": "test_page_1_a_i",
                                    "children": []
                                },
                                {
                                    "title": "test_page_1_a_ii",
                                    "children": []
                                }
                            ]
                        },
                        {
                            "title": "test_page_1_b",
                            "children": []
                        }
                    ]
                },
                {
                    "title": "test_page_2",
                    "children": []
                },
                {
                    "title": "test_page_3",
                    "children": [
                        {
                            "title": "test_page_3_a",
                            "children": []
                        },
                        {
                            "title": "test_page_3_b",
                            "children": []
                        }
                    ]
                }
            ]
        }


# Helpers methods to create factories


def child_path_gen(parent_path):
    """
    Generates iterator of paths given the parent path
    Args:
         parent_path (str): Parent path (format ex: "00010002")
    Yields:
        (str): Child paths (format ex: "000100020001", "000100020002", "000100020003")
    """
    child_num = 0
    while True:
        child_num += 1
        if child_num > 9999:
            # Do not allow more then 9999 children per parent
            raise StopIteration

        child_path_suffix = "000" + str(child_num)
        child_path_suffix = child_path_suffix[:4]
        yield parent_path + child_path_suffix


def create_journal_about_page_factory(journal_structure, about_page_slug=None):
    """
    Creates JournalAboutPageFactory and all of its sub pages that are defined in the journal_structure

    Args:
        journal_structure (dict): defines the structure of the test journal
        about_page_slug (str): desired slug for the journal about page

    Returns:
        (JournalAboutPageFactory): JournalAboutPageFactory that has all the sub pages defined in the
            journal_structure
    """
    title = None
    if 'title' in journal_structure:
        title = journal_structure['title']

    path = "000100010002"
    depth = 3
    children = journal_structure['structure']
    numchild = len(children)
    about_page_factory = JournalAboutPageFactory(
        title=title,
        path=path,
        numchild=numchild,
        depth=depth,
        slug=about_page_slug
    )

    child_path = child_path_gen(path)
    for child in children:
        create_nested_journal_pages(
            journal_page=child,
            path=next(child_path),
            depth=depth + 1,
            slug=child['title']
        )

    return about_page_factory


def create_nested_journal_pages(journal_page, path, depth, slug):
    """
    Creates a JournalPageFactory and all its sub pages that are defined in the journal_page

    Args:
        journal_page (dict): defines attributes of journal page and the structure and attributes of its sub pages
        path (str): page path (format ex: "000300040001")
        depth (int): page depth
        slug (str): page slug

    Returns:
        (JournalPageFactory): JournalPageFactory and it will have also created the JournalPageFactories for its sub
            pages
    """

    title = None
    if 'title' in journal_page:
        title = journal_page['title']

    children = journal_page['children']
    numchild = len(children)
    JournalPageFactory(
        title=title,
        path=path,
        numchild=numchild,
        depth=depth,
        slug=slug
    )

    child_path = child_path_gen(path)
    for child in children:
        create_nested_journal_pages(
            journal_page=child,
            path=next(child_path),
            depth=depth + 1,
            slug=child['title']
        )


# Functions to compare test journals


def is_nested_list_equivalent(actual, expected):
    """
    Return True if actual has the same values and nodes as expected,
    actual may have some extra fields in child dicts, but they should have the same number of nodes
    """
    if len(actual) != len(expected):
        return False

    # the lists may not be sorted, so for every item in expected search through actual to find it
    # once the item has been found, mark that is has been found so we don't recursively compare it again
    for expected_item in expected:
        found_equivalent_item = False

        for actual_item in actual:
            if 'found_equivalent' in actual_item:
                continue

            if is_nested_dict_equivalent(actual_item, expected_item):
                found_equivalent_item = True
                actual_item['found_equivalent'] = True
                break

        # if an equivalent item has not been found for expected_item, these lists are not equivalent
        if not found_equivalent_item:
            return False

    # if an equivalent item was found for all items in expected, these lists are equivalent
    return True


def is_nested_dict_equivalent(actual, expected):
    """
    Return True if actual has the same fields and nodes as expected,
    actual may have some extra fields, but they should have the same number of nodes
    """
    # for each key in expected check whether it is equivalent to the same key in actual
    # if each key represent equivalent dicts, these dicts are equivalent
    for key in expected.keys():
        if not is_nested_json_equivalent(actual[key], expected[key]):
            return False
    return True


def is_nested_json_equivalent(actual, expected):
    """
    Return True if actual has the same fields and nodes as expected,
    actual may have some extra fields, but they should have the same number of nodes
   """
    # expected and actual with either be: None, dict, list or some value
    # different comparisions are required for each case
    if not expected:
        # if expected is false or None actual should also be
        return not actual
    elif isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return is_nested_dict_equivalent(actual, expected)
    elif isinstance(expected, list):
        if not isinstance(actual, list):
            return False
        return is_nested_list_equivalent(actual, expected)
    else:
        return actual == expected