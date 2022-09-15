import requests
import requests.auth

from ..tokens import GITHUB_TOKEN, GITHUB_USERNAME
from ..model import Issue, Repo


GITHUB_BASEURL = "https://api.github.com/repos"
GITHUB_HEADER = {"Authorization": f"token {GITHUB_TOKEN}"}


class ApiError(Exception):
    """Errors raised when Github doesn't answer with expected status_code"""

    pass


def catch_connection_errors(func):
    """Decorator used to prevent URLLib to raise exceptions."""

    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.ConnectionError:
            return None

    return inner


@catch_connection_errors
def fetch_repo(repo: str) -> Repo:
    """
    Fetch a repo by its name.
    Returns a `Repo` instance with issues already provided as `Issue` instance.

    Raise `ApiError` if the status code isn't 200.
    """
    url = f"{GITHUB_BASEURL}/{GITHUB_USERNAME}/{repo}/issues"
    resp = requests.get(url, headers=GITHUB_HEADER)
    if resp.status_code == 200:
        return Repo.from_json(repo, resp.json())
    else:
        raise ApiError(f"Github answered with {resp.status_code}, {resp.text}.")


@catch_connection_errors
def push_new_issue(repo_name: str, issue: Issue) -> bool:
    """
    Push a new `Issue` to a `Repo`.
    Returns `True` iff the issue was created correctly.
    """
    url = f"{GITHUB_BASEURL}/{GITHUB_USERNAME}/{repo_name}/issues"
    resp = requests.post(url, headers=GITHUB_HEADER, data=issue.to_json())
    return resp.status_code == 201


@catch_connection_errors
def update_issue(repo_name, issue: Issue) -> bool:
    """
    Update an already created issue.

    Returns `True` iff the issue was updated correctly.
    """
    url = f"{GITHUB_BASEURL}/{GITHUB_USERNAME}/{repo_name}/issues/{issue.number}"
    resp = requests.patch(url, headers=GITHUB_HEADER, data=issue.to_json())
    return resp.status_code == 200


@catch_connection_errors
def close_issue(repo_name: str, issue: Issue) -> bool:
    """
    Close an issue.

    Returns `True` iff the issue was closed correctly
    """
    issue.close()
    return update_issue(repo_name, issue)
