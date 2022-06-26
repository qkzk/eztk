from .issue import Issue
from ..tokens import GITHUB_USERNAME


class Repo(list):
    """
    Holds a representation of a repository and its issues.

    It inherits some methods from `list` :
    * access to `Issue` by index
    * `len`
    * iteration through issues.

    Exposes a few properties for ease of use :

    * name -> `str`
    * issues -> `list[Issue]`)
    * url -> `str` the web url of the repository.

    """

    def __init__(self, name: str, issues: list[Issue]) -> None:
        """
        name: (str) the name of the repository. Must be the exact name of the repository as in github.
        issues: (list[Issue]) list of holded issues.
        """
        self._name = name
        self._issues: list[Issue] = issues

    @property
    def name(self) -> str:
        """The name of the repository"""
        return self._name

    @property
    def issues(self) -> list[Issue]:
        """The opened issues issues in this repository"""
        return self._issues

    @issues.setter
    def issues(self, issues: list[Issue]):
        """Set a list of issues."""
        self._issues = issues

    @property
    def url(self) -> str:
        """The web url of the repository"""
        return f"https://github.com/{GITHUB_USERNAME}/{self._name}"

    @classmethod
    def from_json(cls, name, json: list) -> "Repo":
        """Creates a `Repo` instance from a JSON sent by github."""
        return cls(
            name,
            [
                Issue.from_json(name, json_issue)
                for json_issue in json
                if json_issue["state"] == "open"
            ],
        )

    def __len__(self) -> int:
        """How many opened issues in this repository ?"""
        return len(self.issues)

    def __getitem__(self, key: int) -> Issue:
        """Access by key"""
        if isinstance(key, int):
            return self.issues[key]
        raise TypeError(f"Index must be int not {type(key)}")

    def __settitem__(self, index: int, issue: Issue):
        """Allow mutability"""
        self.issues[index] = issue

    def __iter__(self):
        """Allow for loops"""
        return self.issues.__iter__()

    def __repr__(self) -> str:
        """Text representation."""
        return f"[{', '.join(map(repr, self.issues))}]"
