from typing import Optional

from textual import log
from textual.app import App, ComposeResult
from textual.containers import (
    Center,
    ScrollableContainer,
    Vertical,
)
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Footer, Header, Markdown, Static


from ..api import fetch_repo, close_issue
from ..commands import open_in_lvim_octo, open_in_ranger, open_in_browser
from ..model import Issue, Repo
from ..tokens import REPOS_DICT


class RepoView(Widget):
    """A repository view widget."""

    DEFAULT_HEIGHT = 5
    """Default height used if children height can't be converted to `cells`."""

    repo = reactive(Repo.empty(), always_update=True)
    """The associated Repo object"""
    selected_index = reactive(0, always_update=True)
    """Index of the selected issue"""

    def __init__(self, index: int):
        super().__init__()
        self.index = index
        """It's own index in repo list"""

    def compose(self) -> ComposeResult:
        """Create child widgets of a RepoView."""
        with Center():
            yield Static(self.repo.name, id="repo_title", classes="repo_title")

    def update_content(self, repo: Repo) -> None:
        """
        Update RepoView content from a new fetched repo.
        - update the repo_title (repo title)
        - remove old issues
        - mount new issues
        """
        self.update_title(repo.name)
        self.update_issues(repo)
        self.update_height()

    def update_issues(self, repo: Repo) -> None:
        """Unmount all issues and mount new ones."""
        self.unmount_issues()
        self.mount_issues(repo)

    def unmount_issues(self) -> None:
        """Unmount all issues"""
        for issue_view in self.query(IssueView):
            issue_view.remove()

    def mount_issues(self, repo: Repo) -> None:
        """Mount new issues"""
        for index, issue in enumerate(repo):
            issue_view = IssueView(index)
            issue_view.issue = issue
            self.mount(issue_view)

    def update_title(self, name: str) -> None:
        """Update the repo_title (the repo name)."""
        self.query_one("#repo_title").update(name)

    def update_height(self) -> None:
        """
        Update self height with child heights.
        It sums every required height of its children and set its own height.

        For some reason I can't do it otherwise.
        """
        self.styles.height = 1 + sum(
            issue_view.styles.height.cells
            if issue_view.styles.height.cells is not None
            else self.DEFAULT_HEIGHT
            for issue_view in self.query(IssueView)
        )

    def select_next_issue(self) -> None:
        """
        Select the next issue. Wrap to the first if needed.
        """
        issues = self.query(IssueView)
        if issues:
            issues[self.selected_index].unselect()
        self.selected_index += 1
        if self.selected_index >= len(self.repo):
            self.selected_index = 0
        if issues:
            issues[self.selected_index].select()

    def select_prev_issue(self):
        """
        Select the previous issue. Wrap to the last if needed.
        """
        issues = self.query(IssueView)
        if issues:
            issues[self.selected_index].unselect()
        self.selected_index -= 1
        if self.selected_index < 0:
            self.selected_index = len(self.repo) - 1
        if issues:
            issues[self.selected_index].select()

    def select(self):
        """
        Set itself as selected and select its first issue.
        """
        self.add_class("selected_repo")
        self.selected_index = 0
        issues = self.query(IssueView)
        if issues:
            issues[0].select()

    def unselect(self):
        """
        Set itself as not selected and select its first issue.
        """
        issues = self.query(IssueView)
        if issues:
            issues[self.selected_index].unselect()
        self.selected_index = 0
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
    """The associated issue object"""

    def __init__(self, index: int):
        super().__init__()
        self.index = index
        """Its own index in the repo"""

    def select(self):
        """Set itself as selected"""
        self.add_class("selected_issue")

    def unselect(self):
        """Set itself as unselected"""
        self.remove_class("selected_issue")

    def on_click(self) -> None:
        """Action when an issue is clicked: toggle the display"""
        repo_view = self.parent
        app = self.parent.parent.parent.parent
        app.select_issue_by_index(repo_view.index, self.index)
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
        ("q", "quit", "quit"),
        ("d", "toggle_dark", "Dark mode"),
        ("up", "prev_issue", "Previous issue"),
        ("down", "next_issue", "Next issue"),
        ("left", "prev_repo", "Previous repo"),
        ("right", "next_repo", "Next repo"),
        ("enter", "toggle_issue", "Toggle issue"),
        ("g", "github_issue", "Github issue"),
        ("G", "github_repo", "Github repo"),
        ("o", "octo", "Octo"),
        ("r", "ranger", "Ranger"),
        ("x", "close", "Close"),
    ]
    __repos_dict = REPOS_DICT
    """A dict of repo name: folder address"""
    __repos_list = reactive(list[Repo], always_update=True)
    """A list of associated repo object"""
    selected_index = reactive(0)
    """Index of the selected repo view"""

    def on_load(self):
        """Run on start, before compose"""
        self.reload_repos()

    def on_mount(self):
        """
        Run after compose.
        Refresh the content and set an interval to call it again every 30s
        """
        self.refresh_content()
        self.set_interval(30, self.refresh_content)

    def refresh_content(self) -> None:
        """
        Reload the repos, display the repos, select the first.
        """
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
        """Associate every fetched and parsed repo to its view."""
        for repo_view, repo in zip(self.query(RepoView), self.__repos_list):
            repo_view.repo = repo
            log(repo_view.repo.name, repo.name)
            repo_view.update_content(repo)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(id="header")
        yield Footer()
        yield ScrollableContainer(
            *(RepoView(index) for index in range(len(self.__repos_list)))
        )

    def select_first(self) -> None:
        """Select the first repos. Doesn't change the selected index."""
        repo = self.query(RepoView)[0]
        repo.select()
        issue_views = repo.query("IssueView")
        if issue_views:
            issue_views[0].select()

    def selected_issue_view(self) -> Optional[IssueView]:
        """
        Return the selected issue view if any. None otherwise.
        It should always be tested against None since repos may have 0 issue.
        """
        repo = self.query("RepoView")[self.selected_index]
        issue_views = repo.query(IssueView)
        if issue_views:
            return issue_views[repo.selected_index]

    def selected_repo_view(self) -> RepoView:
        """Returns the selected RepoView"""
        return self.query(RepoView)[self.selected_index]

    def selected_address(self) -> str:
        return self.__repos_dict.get(self.__repos_list[self.selected_index].name, "")

    def select_issue_by_index(self, repo_index: int, issue_index: int) -> None:
        """Select a repo and an issue from their indeces."""
        self.selected_repo_view().unselect()
        self.selected_index = repo_index
        repo = self.query(RepoView)[repo_index]
        repo.select()
        issue_views = repo.query(IssueView)
        if issue_index < len(issue_views):
            issue_views[issue_index].select()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_next_repo(self) -> None:
        """An action to select the next repo"""
        self.selected_repo_view().unselect()
        self.selected_index += 1
        if self.selected_index >= len(self.__repos_list):
            self.selected_index = 0
        self.selected_repo_view().select()

    def action_prev_repo(self) -> None:
        """An action to select the previous repo"""
        self.selected_repo_view().unselect()
        self.selected_index -= 1
        if self.selected_index < 0:
            self.selected_index = len(self.__repos_list) - 1
        self.selected_repo_view().select()

    def action_next_issue(self) -> None:
        """An action to select the next issue"""
        self.selected_repo_view().select_next_issue()

    def action_prev_issue(self) -> None:
        """An action to select the previous issue"""
        self.selected_repo_view().select_prev_issue()

    def action_toggle_issue(self) -> None:
        """An action to toggle the body of the selected issue"""
        issue_view = self.selected_issue_view()
        if issue_view is not None:
            issue_view.toggle_text_display()

    def action_github_issue(self) -> None:
        """An action to open the issue in github"""
        issue_view = self.selected_issue_view()
        if issue_view is not None:
            open_in_browser(issue_view.issue.url)

    def action_github_repo(self) -> None:
        """An action to open the selected repo in github"""
        open_in_browser(self.selected_repo_view().repo.url)

    def action_ranger(self) -> None:
        """An action to open the selected issue in github"""
        open_in_ranger(self.selected_address())

    def action_octo(self) -> None:
        """An action to open the issue in nvim Octo plugin"""
        issue_view = self.selected_issue_view()
        if issue_view:
            open_in_lvim_octo(self.selected_address(), issue_view.issue.number)

    def action_close(self) -> None:
        """An action to close the issue"""
        issue_view = self.selected_issue_view()
        if issue_view is not None:
            repo_name = self.selected_repo_view().repo.name
            close_issue(repo_name, issue_view.issue)
