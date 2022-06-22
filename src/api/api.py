import json
import requests
import requests.auth

from ..tokens import GITHUB_TOKEN, GITHUB_USERNAME
from ..model import Issue, Repo


GITHUB_BASEURL = "https://api.github.com/repos"
GITHUB_HEADER = {"Authorization": f"token {GITHUB_TOKEN}"}


class ApiError(Exception):
    pass


def fetch_repo(repo: str) -> Repo:
    url = f"{GITHUB_BASEURL}/{GITHUB_USERNAME}/{repo}/issues"
    resp = requests.get(url, verify=False, headers=GITHUB_HEADER)
    if resp.status_code == 200:
        return Repo.from_json(repo, resp.json())
    else:
        raise ApiError(f"Github answered with {resp.status_code}, {resp.text}.")


def push_new_issue(repo_name: str, issue: Issue) -> bool:
    url = f"{GITHUB_BASEURL}/{GITHUB_USERNAME}/{repo_name}/issues"
    resp = requests.post(url, headers=GITHUB_HEADER, data=issue.to_json())
    return resp.status_code == 201


def update_issue(repo_name, issue: Issue) -> bool:
    url = f"{GITHUB_BASEURL}/{GITHUB_USERNAME}/{repo_name}/issues/{issue.number}"
    resp = requests.patch(url, headers=GITHUB_HEADER, data=issue.to_json())
    return resp.status_code == 200
