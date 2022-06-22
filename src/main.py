from .api import fetch_repo, push_new_issue, update_issue
from .model import Issue


def test_api():
    cours_nsi = fetch_repo("cours-nsi")

    issue = Issue("titre", "corps", ["a", "b"], -1, "open")
    is_created = push_new_issue("cours-nsi", issue)
    assert is_created, "Couldn't create the issue"

    cours_nsi = fetch_repo("cours-nsi")
    issue = cours_nsi[0]
    assert isinstance(issue, Issue), "__getitem__[0] devrait renvoyer une Issue"

    issue.body = "nouveau body"
    issue.labels = ["a", "b", "c"]
    is_updated = update_issue("cours-nsi", issue)
    assert is_updated, "Couldn't update the issue"
