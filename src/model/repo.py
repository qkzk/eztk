from .issue import Issue
from ..tokens import GITHUB_USERNAME


class Repo(list):
    def __init__(self, name: str, issues: list[Issue]) -> None:
        self._name = name
        self._issues: list[Issue] = issues

    @property
    def name(self) -> str:
        return self._name

    @property
    def issues(self) -> list[Issue]:
        return self._issues

    @issues.setter
    def issues(self, issues: list[Issue]):
        self._issues = issues

    @property
    def url(self) -> str:
        return f"https://github.com/{GITHUB_USERNAME}/{self._name}"

    @classmethod
    def from_json(cls, name, json: list):
        return cls(
            name,
            [
                Issue.from_json(name, json_issue)
                for json_issue in json
                if json_issue["state"] == "open"
            ],
        )

    def __len__(self) -> int:
        return len(self.issues)

    def __getitem__(self, key: int) -> Issue:
        if isinstance(key, int):
            return self.issues[key]
        raise TypeError(f"Index must be int not {type(key)}")

    def __settitem__(self, index: int, issue: Issue):
        self.issues[index] = issue

    def __iter__(self):
        return self.issues.__iter__()

    def __repr__(self) -> str:
        return f"[{', '.join(map(repr, self.issues))}]"
