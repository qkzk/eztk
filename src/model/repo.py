from .issue import Issue


class Repo(list):
    def __init__(self, name: str, issues: list[Issue]) -> None:
        self._name = name
        self._issues: list[Issue] = issues

    @property
    def issues(self) -> list[Issue]:
        return self._issues

    @issues.setter
    def issues(self, issues: list[Issue]):
        self._issues = issues

    @classmethod
    def from_json(cls, name, json: list):
        return cls(
            name,
            [
                Issue.from_json(json_issue)
                for json_issue in json
                if json_issue["state"] == "open"
            ],
        )

    def __len__(self) -> int:
        return len(self.issues)

    def __getitem__(self, key: int | slice) -> Issue | list[Issue]:
        if isinstance(key, int):
            return self.issues[key]
        if isinstance(key, slice):
            return self.issues[key]
        raise TypeError(f"Index must be int or slice not {type(key)}")

    def __settitem__(self, index: int, issue: Issue):
        self.issues[index] = issue

    def __repr__(self) -> str:
        return f"[{', '.join(map(repr, self.issues))}]"
