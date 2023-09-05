from textual import log
from textual.app import App, ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, Label, Markdown, Static

from src.model.repo import Repo

from ..api import fetch_repo
from ..model import Issue
from ..tokens import REPOS_DICT

DEV_TEXT = """_italic_ **bold**

```python
print(1)
```
- [ ] unckecked
- [x] checked

1. one
2. two
"""


class RepoView(Static):
    """A repository view widget."""

    DEFAULT_HEIGHT = 5
    """Default height used if children height can't be converted to `cells`."""

    repo = reactive(Repo.empty())

    def compose(self) -> ComposeResult:
        """Create child widgets of a RepoView."""
        yield Label(self.repo.name, id="label")
        for _ in range(len(self.repo)):
            yield IssueView()

    def update_content(self, repo: Repo):
        log("RepoView: update_content", repo)
        self.repo = repo
        label = self.query_one(Label)
        label.update(self.repo.name)
        label.refresh(layout=True, repaint=True)
        log("label", label)
        for issue_view, issue in zip(self.query(IssueView), self.repo):
            issue_view.issue = issue

    def update_height(self) -> None:
        """
        Update self height with child heights.
        It sums every required height of its children and set its own height.

        For some reason I can't do it otherwise.
        """
        self.styles.height = sum(
            issue_view.styles.height.cells
            if issue_view.styles.height.cells is not None
            else self.DEFAULT_HEIGHT
            for issue_view in self.query(IssueView)
        )


class IssueView(Static):
    """An IssueView widget"""

    BUTTON_HEIGHT = 5
    """Height of the button line"""
    PADDING_HEIGHT = 3
    """Padding around issue text"""
    DEFAULT_LINE_WIDTH = 60
    """Default line width of text display"""

    is_text_open = reactive(False)
    """True iff the issue view text is displayed"""

    issue = reactive(Issue.empty())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        if event.button.id == "title":
            self.__toggle_text_display()
        elif event.button.id == "edit":
            self.__edit()
        elif event.button.id == "close":
            self.__close()

    def __toggle_text_display(self):
        """
        Toggle between text and no text display.
        Update its size and the size of its container.
        """
        self.is_text_open = not self.is_text_open
        content = self.query_one(Markdown)
        content.update(self.__issue_text)
        content.toggle_class("display")
        content.toggle_class("none")
        self.styles.height = self.required_height(content)
        self.parent.update_height()

    @property
    def __issue_text(self) -> str:
        """Returns the displayed text depending if it's open or not."""
        if self.is_text_open:
            return self.issue.body
        else:
            return ""

    def required_height(self, content: Markdown) -> int:
        """Calculates its required height."""
        if self.is_text_open:
            return (
                content.get_content_height(
                    self.size, self.container_viewport, self.DEFAULT_LINE_WIDTH
                )
                + self.PADDING_HEIGHT
                + self.BUTTON_HEIGHT
            )
        else:
            return self.BUTTON_HEIGHT

    def __edit(self):
        pass

    def __close(self):
        pass

    def on_mount(self):
        pass

    def compose(self) -> ComposeResult:
        """Creates child widget of an IssueView."""
        with Vertical(id="issue_view_vertical"):
            with Horizontal(id="issue_view_top_bar"):
                yield Button(self.issue.title, id="title", variant="success")
                yield Button("Edit", id="edit", variant="warning")
                yield Button("Close", id="close", variant="error")
            yield Markdown(self.__issue_text, id="issue_view_text", classes="none")


class EZView(App):
    """A Textual app to manage stopwatches."""

    TITLE = "EZTK"
    CSS_PATH = "ui.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"), ("q", "quit", "quit")]
    __repos_dict = REPOS_DICT
    __repos_content = reactive(list[Repo])

    def on_load(self):
        """Run on start, before compose"""
        log("EZView: on_load")
        self.reload_repos()

    def on_mount(self):
        """Run after compose"""
        log("EZView: on_mount")
        self.set_interval(1, self.refresh_content)

    def refresh_content(self) -> None:
        log("EZView: refresh_content")
        self.reload_repos()
        self.dispatch_repos()

    def reload_repos(self) -> None:
        """
        Fetch the repos.
        Since the `Repo` object inherit from `list`, we can set it to
        an empty `list`
        when the request returns `None` (ie. when `requests` encountered
        a connexion error.)
        """
        for name in self.__repos_dict:
            response = fetch_repo(name)
            # log(f"repo {name}")
            # log(response)
            self.__repos_content.append(response)

    def dispatch_repos(self) -> None:
        for repo_view, repo in zip(self.query(RepoView), self.__repos_content):
            repo_view.update_content(repo)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        log("EZView: compose")
        yield Header(id="header")
        yield Footer()
        yield ScrollableContainer(
            *(RepoView() for _ in range(len(self.__repos_content)))
        )

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark
