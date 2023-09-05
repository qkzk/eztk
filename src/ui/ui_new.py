from textual import events, log
from textual.app import App, ComposeResult
from textual.containers import (
    Center,
    Container,
    Horizontal,
    ScrollableContainer,
    Vertical,
)
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Footer, Header, Label, Markdown, Static

from src.model.repo import Repo

from ..api import fetch_repo
from ..model import Issue
from ..tokens import REPOS_DICT


class RepoView(Container):
    """A repository view widget."""

    DEFAULT_HEIGHT = 5
    """Default height used if children height can't be converted to `cells`."""

    repo = reactive(Repo.empty())

    def compose(self) -> ComposeResult:
        """Create child widgets of a RepoView."""
        with Center():
            yield Static(self.repo.name, id="repo_title", classes="repo-title")

    def update_content(self, repo: Repo):
        """
        Update RepoView content from a new fetched repo.
        - update the repo_title (repo title)
        - remove old issues
        - mount new issues
        """
        self.update_title(repo.name)
        self.update_issues(repo)
        self.update_height()
        self.repo = repo

    def update_issues(self, repo: Repo):
        """Unmount all issues and mount new ones."""
        self.unmount_issues()
        self.mount_issues(repo)

    def unmount_issues(self):
        """Unmount all issues"""
        for issue_view in self.query(IssueView):
            issue_view.remove()

    def mount_issues(self, repo: Repo):
        """Mount new issues"""
        for issue in repo:
            issue_view = IssueView()
            issue_view.issue = issue
            self.mount(issue_view)

    def update_title(self, name: str):
        """Update the repo_title (the repo name)."""
        self.query_one("#repo_title").update(name)

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


class IssueView(Container):
    """An IssueView widget"""

    DEFAULT_HEIGHT = 1
    """Height of the button line"""
    PADDING_HEIGHT = 3
    """Padding around issue text"""
    DEFAULT_LINE_WIDTH = 60
    """Default line width of text display"""

    is_text_open = reactive(False)
    """True iff the issue view text is displayed"""

    issue = reactive(Issue.empty())

    def on_click(self) -> None:
        self.__toggle_text_display()

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
                + self.DEFAULT_HEIGHT
            )
        else:
            return self.DEFAULT_HEIGHT

    def compose(self) -> ComposeResult:
        """Creates child widget of an IssueView."""
        with Vertical(id="issue_view_vertical"):
            yield Static(self.issue.title, id="title", classes="issue-title")
            yield Markdown(self.__issue_text, id="issue_view_text", classes="none")


class EZView(App):
    """A Textual app to manage stopwatches."""

    TITLE = "EZTK"
    CSS_PATH = "ui.tcss"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "quit"),
    ]
    __repos_dict = REPOS_DICT
    __repos_content = reactive(list[Repo])
    __selected_issue = reactive(IssueView)

    def on_load(self):
        """Run on start, before compose"""
        self.reload_repos()

    def on_mount(self):
        """Run after compose"""
        self.refresh_content()
        self.set_interval(30, self.refresh_content)

    def refresh_content(self) -> None:
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
        repos_content = []
        for name in self.__repos_dict:
            response = fetch_repo(name)
            repos_content.append(response)
        self.__repos_content = repos_content

    def dispatch_repos(self) -> None:
        i = 0
        for repo_view, repo in zip(self.query(RepoView), self.__repos_content):
            i += 1
            repo_view.update_content(repo)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(id="header")
        yield Footer()
        yield ScrollableContainer(
            *(RepoView() for _ in range(len(self.__repos_content)))
        )

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def on_mouse_move(self, event: events.MouseMove) -> None:
        t = ""
        titles = self.query(".issue-title")
        for title in titles:
            if (
                title.has_pseudo_class("hover")
                or title.parent.parent.has_pseudo_class("hover")
                or title.parent.parent.query_one(Markdown).has_pseudo_class("hover")
            ):
                t = title.parent.parent.issue.title
                self.__selected_issue = title.parent.parent

        log(f"on_mouse_move: {event} title {t}")
