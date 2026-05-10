import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from etl_github import parse_github_date, extract_issue_number

def test_extract_issue_number():
    assert extract_issue_number("Fix #123 bug") == 123
    assert extract_issue_number("Closes #456 and #789") == 456
    assert extract_issue_number("No issue here") is None

def test_parse_github_date():
    dt = parse_github_date("2025-04-30T14:22:10Z")
    assert dt is not None
    assert dt.year == 2025