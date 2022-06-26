from __future__ import annotations
import json

from ..tokens import GITHUB_USERNAME


class Issue:
    """
    Holds a representation of an issue in github.
    """

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
        """Text representation."""
        return f"Issue({self.title}, {self.body}, {self.labels}, {self.number})"

    @property
    def repo(self) -> str:
        """The name of parent repository."""
        return self._repo

    @property
    def title(self) -> str:
        """Issue title"""
        return self._title

    @title.setter
    def title(self, title: str):
        """Set the title"""
        self._title = title

    @property
    def body(self) -> str:
        """Body content"""
        return self._body

    @body.setter
    def body(self, body: str):
        """Set the body"""
        self._body = body

    @property
    def labels(self) -> list[str]:
        """Labels (tags) as list of strings."""
        return self._labels

    @labels.setter
    def labels(self, labels: list[str]):
        """Set the labels from a list of strings."""
        self._labels = labels

    @property
    def labels_str(self) -> str:
        """Returns a string of labels, separated by spaces"""
        return " ".join(self.labels) if self.labels else ""

    @property
    def number(self) -> int:
        """The issue number. Unique id of the issue **in this repository**."""
        return self._number

    @property
    def state(self) -> str:
        """State ('open', 'close') of the issue."""
        return self._state

    @property
    def close(self) -> None:
        """Set the state to "close"."""
        self._state = "close"

    def set_labels_from_str(self, str_labels: str) -> None:
        """
        Set the labels from a space separated string of labels
        "a b c" -> ["a", "b", "c"]
        """
        self.labels = str_labels.split(" ")

    @property
    def url(self) -> str:
        """The _web_ url of the issue."""
        return f"https://github.com/{GITHUB_USERNAME}/{self.repo}/issues/{self.number}"

    @classmethod
    def from_json(cls, repo: str, json_issue: dict) -> Issue:
        """Returns an instance of `Issue` parsed from a JSON sent by Github."""
        return cls(
            repo,
            json_issue["title"],
            json_issue["body"],
            cls.parse_labels(json_issue["labels"]),
            int(json_issue["number"]),
            json_issue["state"],
        )

    @staticmethod
    def parse_labels(json_labels: dict) -> list[str]:
        """Parse the labels received by github."""
        return [json_label["name"] for json_label in json_labels]

    def to_json(self) -> str:
        """Returns a github compatible representation of the `Issue`."""
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
