"""
    Unit testing module for course_commands.py.
"""
from shell import SchedulerShell
from io import StringIO
from contextlib import redirect_stdout
from unittest.mock import patch
import importlib
import shell
import course_commands
importlib.reload(shell)
importlib.reload(course_commands)


import course_commands

print("COURSE COMMANDS LOADED FROM:")
print(course_commands.__file__)
"""
    Tests: 
    1. Adding a course with no file provided
    2. Adding a course with a file that does not exist
    3. Adding a course with an empty file
    4. Adding a course with an invalid file type
    5. Adding a course with an invalid configuration
"""

TESTS_FAILED = 0
TESTS_PASSED = 0

"""Test 1"""
def test_course_add_no_file_provided():

    print("****************************************")
    print("Test 1:\t\tAdding a course with no file provided")

    expected = "No configuration file selected"

    output = StringIO()

    with redirect_stdout(output):
        testshellcourse.do_course("add ")

    actual = output.getvalue().strip()

    print(f"Expected:\t{expected}")
    print(f"Actual:\t\t{actual}")

    if actual == expected:
        print("PASSED")
        global TESTS_PASSED
        TESTS_PASSED += 1
    else:
        global TESTS_FAILED
        TESTS_FAILED += 1
        print("FAILED")

"""Test 2"""
def test_course_add_file_that_does_not_exist():
    print("****************************************")
    print("Test 2:\t\tAdding a course with a file that does not exist")

    expected = "Failed to add course due to system error: [Errno 2] No such file or directory: 'json_files/nonexistent.json'"

    output = StringIO()

    with redirect_stdout(output):
        try: 
            testshellcourse.do_course("add json_files/nonexistent.json")
        except FileNotFoundError as e:
            print(f"Error: {e}")

    actual = output.getvalue().strip()

    print(f"Expected:\t{expected}")
    print(f"Actual:\t\t{actual}")

    if actual == expected:
        print("PASSED")
        global TESTS_PASSED
        TESTS_PASSED += 1
    else:
        print("FAILED")
        global TESTS_FAILED
        TESTS_FAILED += 1

"""Test 3"""
def test_course_add_empty_file():
    print("****************************************")
    print("Test 3:\t\tAdding a course with an empty file")

    expected = "Failed to add course due to system error: Expecting value: line 1 column 1 (char 0)"

    output = StringIO()

    with redirect_stdout(output):
        try: 
            testshellcourse.do_course("add json_files/test_empty.json")
        except Exception as e:
            print(f"Error: {e}")

    actual = output.getvalue().strip()

    print(f"Expected:\t{expected}")
    print(f"Actual:\t\t{actual}")

    if actual == expected:
        print("PASSED")
        global TESTS_PASSED
        TESTS_PASSED += 1
    else:
        print("FAILED")
        global TESTS_FAILED
        TESTS_FAILED += 1

"""Test 4"""
def test_course_add_invalid_filetype():
    print("****************************************")
    print("Test 4:\t\tAdding a course with an invalid file type")

    expected = "File 'json_files/test_invalid.txt' is not a valid JSON file."

    output = StringIO()

    with patch("builtins.input", side_effect=[
        "150",
        "33",
        "4",
        "25",
        "online",
        "",
        "",
        "n",
        "",
        ""
    ]):
        with redirect_stdout(output):
            testshellcourse.do_course(
                "add json_files/test_not_json.txt"
            )

    actual = output.getvalue().strip()

    print(f"Expected:\t{expected}")
    print(f"Actual:\t\t{actual}")

    if actual == expected:
        print("PASSED")
        global TESTS_PASSED
        TESTS_PASSED += 1
        return
    else:
        print("FAILED")
        global TESTS_FAILED
        TESTS_FAILED += 1
        return


def test_course_add_invalid_configuration():
    print("****************************************")
    print("Test 5:\t\tAdding a course with an invalid configuration")

    expected = "Configuration file is invalid. Please provide a valid configuration file."

    output = StringIO()

    with patch("builtins.input", side_effect=[
        "150",
        "33",
        "4",
        "25",
        "online",
        "",
        "",
        "n",
        "",
        ""
    ]):
        with redirect_stdout(output):
            testshellcourse.do_course(
                "add json_files/test_invalid.json"
            )

    actual = output.getvalue().strip()

    print(f"Expected:\t{expected}")
    print(f"Actual:\t\t{actual}")

    if actual == expected:
        print("PASSED")
        global TESTS_PASSED
        TESTS_PASSED += 1
        return
    else:
        print("FAILED")
        global TESTS_FAILED
        TESTS_FAILED += 1
        return


if __name__ == "__main__":

    testshellcourse = SchedulerShell()
    test_course_add_no_file_provided()
    test_course_add_file_that_does_not_exist()
    test_course_add_empty_file()
    test_course_add_invalid_filetype()
    test_course_add_invalid_configuration()

    print("****************************************")
    print(f"Tests Passed: {TESTS_PASSED}")
    print(f"Tests Failed: {TESTS_FAILED}")
