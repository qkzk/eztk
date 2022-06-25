import requests
import requests.auth

from ..tokens import GITHUB_TOKEN, GITHUB_USERNAME
from ..model import Issue, Repo


GITHUB_BASEURL = "https://api.github.com/repos"
GITHUB_HEADER = {"Authorization": f"token {GITHUB_TOKEN}"}


class ApiError(Exception):
    pass


def catch_connection_errors(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.ConnectionError:
            return None

    return inner


@catch_connection_errors
def fetch_repo(repo: str) -> Repo:
    url = f"{GITHUB_BASEURL}/{GITHUB_USERNAME}/{repo}/issues"
    resp = requests.get(url, headers=GITHUB_HEADER)
    if resp.status_code == 200:
        return Repo.from_json(repo, resp.json())
    else:
        raise ApiError(f"Github answered with {resp.status_code}, {resp.text}.")


@catch_connection_errors
def push_new_issue(repo_name: str, issue: Issue) -> bool:
    url = f"{GITHUB_BASEURL}/{GITHUB_USERNAME}/{repo_name}/issues"
    resp = requests.post(url, headers=GITHUB_HEADER, data=issue.to_json())
    return resp.status_code == 201


@catch_connection_errors
def update_issue(repo_name, issue: Issue) -> bool:
    url = f"{GITHUB_BASEURL}/{GITHUB_USERNAME}/{repo_name}/issues/{issue.number}"
    resp = requests.patch(url, headers=GITHUB_HEADER, data=issue.to_json())
    return resp.status_code == 200
