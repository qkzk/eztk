from typing import Optional
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
from src.api.api import close_issue
from src.commands.term import open_in_lvim_octo, open_in_ranger

from src.commands.web import open_in_browser


from ..api import fetch_repo
from ..model import Repo
from ..model import Issue
from ..tokens import REPOS_DICT


class RepoView(Widget):
    """A repository view widget."""

    DEFAULT_HEIGHT = 5
    """Default height used if children height can't be converted to `cells`."""

    repo = reactive(Repo.empty(), always_update=True)
    selected = reactive(0, always_update=True)

    def compose(self) -> ComposeResult:
        """Create child widgets of a RepoView."""
        with Center():
            yield Static(self.repo.name, id="repo_title", classes="repo_title")

    def update_content(self, repo: Repo):
        """
        Update RepoView content from a new fetched repo.
        - update the repo_title (repo title)
        - remove old issues
        - mount new issues
        """
        log("update content", len(self.repo))
        self.update_title(repo.name)
        self.update_issues(repo)
        self.update_height()

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

    def select_next_issue(self):
        issues = self.query(IssueView)
        if issues:
            issues[self.selected].unselect()
        self.selected += 1
        if self.selected >= len(self.repo):
            self.selected = 0
        issues[self.selected].select()

    def select_prev_issue(self):
        issues = self.query(IssueView)
        if issues:
            issues[self.selected].unselect()
        self.selected -= 1
        if self.selected < 0:
            self.selected = len(self.repo) - 1
        issues[self.selected].select()

    def select(self):
        self.add_class("selected_repo")
        self.selected = 0
        issues = self.query(IssueView)
        if issues:
            issues[0].select()

    def unselect(self):
        issues = self.query(IssueView)
        if issues:
            issues[self.selected].unselect()
        self.selected = 0
        self.remove_class("selected_repo")


class IssueView(Widget):
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

    def select(self):
        self.add_class("selected_issue")

    def unselect(self):
        self.remove_class("selected_issue")

    def on_click(self) -> None:
        self.toggle_text_display()

    def toggle_text_display(self):
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
        ("up", "prev_issue", "Select previous issue"),
        ("down", "next_issue", "Select next issue"),
        ("left", "prev_repo", "Select previous repo"),
        ("right", "next_repo", "Select previous repo"),
        ("enter", "toggle_issue", "Toggle issue"),
        ("g", "github_issue", "Github issue"),
        ("G", "github_repo", "Github repo"),
        ("o", "octo", "Octo"),
        ("r", "ranger", "Ranger"),
        ("x", "close", "Close"),
    ]
    __repos_dict = REPOS_DICT
    __repos_list = reactive(list[Repo])
    selected = reactive(0)

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
        self.select_first()

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
        self.__repos_list = repos_content

    def dispatch_repos(self) -> None:
        for repo_view, repo in zip(self.query(RepoView), self.__repos_list):
            repo_view.repo = repo
            log(repo_view.repo.name, repo.name)
            repo_view.update_content(repo)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(id="header")
        yield Footer()
        yield ScrollableContainer(*(RepoView() for _ in range(len(self.__repos_list))))

    def select_first(self):
        repo = self.query("RepoView")[0]
        repo.select()
        issue_views = repo.query("IssueView")
        if issue_views:
            issue_views[0].select()

    def selected_issue_view(self) -> Optional[IssueView]:
        repo = self.query("RepoView")[self.selected]
        issue_views = repo.query(IssueView)
        if issue_views:
            return issue_views[repo.selected]

    def selected_repo_view(self) -> RepoView:
        return self.query("RepoView")[self.selected]

    def selected_address(self) -> str:
        return self.__repos_dict.get(self.__repos_list[self.selected].name, "")

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_next_repo(self) -> None:
        self.selected_repo_view().unselect()
        self.selected += 1
        if self.selected >= len(self.__repos_list):
            self.selected = 0
        self.selected_repo_view().select()

    def action_prev_repo(self) -> None:
        self.selected_repo_view().unselect()
        self.selected -= 1
        if self.selected < 0:
            self.selected = len(self.__repos_list) - 1
        self.selected_repo_view().select()

    def action_next_issue(self):
        self.selected_repo_view().select_next_issue()

    def action_prev_issue(self):
        self.selected_repo_view().select_prev_issue()

    def action_toggle_issue(self):
        issue_view = self.selected_issue_view()
        if issue_view is not None:
            issue_view.toggle_text_display()

    def action_github_issue(self):
        issue_view = self.selected_issue_view()
        if issue_view is not None:
            open_in_browser(issue_view.issue.url)

    def action_github_repo(self):
        open_in_browser(self.selected_repo_view().repo.url)

    def action_ranger(self):
        open_in_ranger(self.selected_address())

    def action_octo(self):
        issue_view = self.selected_issue_view()
        if issue_view:
            open_in_lvim_octo(self.selected_address(), issue_view.issue.number)

    def action_close(self):
        issue_view = self.selected_issue_view()
        if issue_view is not None:
            repo_name = self.selected_repo_view().repo.name
            close_issue(repo_name, issue_view.issue)
