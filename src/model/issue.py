import json

from ..tokens import GITHUB_USERNAME


class Issue:
    def __init__(
        self,
        repo: str,
        title: str,
        body: str,
        labels: list[str],
        number: int,
        state: str,
    ):
        self._repo = repo
        self._body = body
        self._title = title
        self._labels = labels
        self._number = number
        self._state = state

    def __repr__(self) -> str:
        return f"Issue({self.title}, {self.body}, {self.labels}, {self.number})"

    @property
    def repo(self) -> str:
        return self._repo

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, title: str):
        self._title = title

    @property
    def body(self) -> str:
        return self._body

    @body.setter
    def body(self, body: str):
        self._body = body

    @property
    def labels(self) -> list[str]:
        return self._labels

    @labels.setter
    def labels(self, labels: list[str]):
        self._labels = labels

    @property
    def labels_str(self) -> str:
        return " ".join(self.labels) if self.labels else ""

    @property
    def number(self) -> int:
        return self._number

    @property
    def state(self) -> str:
        return self._state

    @property
    def close(self):
        self._state = "close"

    def set_labels_from_str(self, str_labels: str):
        self.labels = str_labels.split(" ")

    def get_labels_str(self) -> str:
        return " ".join(self.labels)

    @property
    def url(self) -> str:
        return f"https://github.com/{GITHUB_USERNAME}/{self.repo}/issues/{self.number}"

    @classmethod
    def from_json(cls, repo: str, json_issue: dict) -> "Issue":
        return cls(
            repo,
            json_issue["title"],
            json_issue["body"],
            cls.parse_labels(json_issue["labels"]),
            int(json_issue["number"]),
            json_issue["state"],
        )

    def to_json(self) -> str:
        return json.dumps(
            {
                "title": self.title,
                "body": self.body,
                "labels": self.labels,
                "state": self.state,
            },
            indent=None,
            separators=(",", ":"),
        )

    @staticmethod
    def parse_labels(json_labels: dict) -> list[str]:
        return [json_label["name"] for json_label in json_labels]
