import math
from rich.columns import Columns
from rich.panel import Panel
from rich.text import Text

from textual import events
from textual.app import App
from textual.reactive import Reactive
from textual.widget import Widget

from ..api import fetch_repo
from ..commands import open_in_browser, open_in_ranger, open_in_lvim_octo
from ..model import Issue
from ..tokens import REPOS_DICT
from .colors import COLORS

LEFT_BUTTON = 1
RIGHT_BUTTON = 3


class IssueView(Widget):
    is_repo_selected: Reactive[bool] = Reactive(False)
    text_color: Reactive[str] = Reactive("grey70")
    selected_issue_color: Reactive[str]

    def on_mount(self) -> None:
        self.set_interval(1, self.refresh)

    def render(self) -> Text:
        return Text(
            self.issue.title,
            style=self.text_color,
            overflow="ellipsis",
            no_wrap=True,
        )

    def with_issue(self, issue: Issue) -> "IssueView":
        self.issue = issue
        return self

    def with_selected_color(self, color: str) -> "IssueView":
        self.selected_issue_color = color
        return self

    def set_selected(self) -> None:
        self.text_color = self.selected_issue_color + " bold italic"

    def set_repo_selected(self) -> None:
        self.is_repo_selected = True
        self.text_color = "grey90 bold"

    def set_repo_not_selected(self) -> None:
        self.is_repo_selected = False
        self.text_color = "grey50"


class IssueDetail(Widget):
    is_repo_selected: Reactive[bool] = Reactive(False)
    border_style: Reactive[str]
    issue: Reactive[Issue]

    def with_issue(self, issue: Issue) -> "IssueDetail":
        self.issue = issue
        return self

    def with_border_style(self, color: str) -> "IssueDetail":
        self.border_style = color
        return self

    def render(self) -> Panel:
        return Panel(
            self.issue.body,
            title=self.issue.title,
            subtitle=self.issue.labels_str,
            style=self.color,
            border_style=self.border_style,
        )

    @property
    def color(self) -> str:
        return "grey100 bold" if self.is_repo_selected else "grey100"

    def set_repo_selected(self) -> None:
        self.is_repo_selected = True

    def set_repo_not_selected(self) -> None:
        self.is_repo_selected = False


class RepoView(Widget):
    is_selected: Reactive[bool] = Reactive(False)
    nb_issues: Reactive[int] = Reactive(0)
    selected_index: Reactive[int] = Reactive(0)
    has_issues: Reactive[bool] = Reactive(False)
    index: Reactive[int]

    def on_mount(self) -> None:
        self.set_interval(1, self.refresh)
        self.set_interval(30, self.reload_repos)
        self.reload_repos()

    def set_index(self, index: int) -> None:
        self.index = index

    def reload_repos(self) -> None:
        self.repo = fetch_repo(self._name)

    def generate_content(self) -> list:
        self.nb_issues = len(self.repo)
        if self.nb_issues == 0:
            self.has_issues = False
            return [" "]

        self.has_issues = True
        content: list[IssueView | IssueDetail]
        content = [
            IssueView().with_issue(issue).with_selected_color(self.border_style)
            for issue in self.repo
        ]
        if self.is_selected:
            self.select_all_views(content)
        content[self.selected_index].set_selected()
        content.append(self.generate_issue_detail())
        return content

    @staticmethod
    def select_all_views(content: list[IssueView | IssueDetail]):
        for view in content:
            view.set_repo_selected()

    def generate_issue_detail(self) -> IssueDetail:
        return (
            IssueDetail()
            .with_issue(self.repo[self.selected_index])
            .with_border_style(self.border_style)
        )

    @property
    def border_style(self) -> str:
        return f"{COLORS[self.index % len(COLORS)]}" + (
            " bold italic" if self.is_selected else ""
        )

    def render(self) -> Panel:
        return Panel(
            Columns(self.generate_content()),
            title=self._name,
            border_style=self.border_style,
        )

    def set_name(self, name: str) -> None:
        self._name = name

    def set_address(self, address: str) -> None:
        self._address = address

    def is_in_issues_list(self, y: int) -> bool:
        return self.has_issues and y <= len(self.repo)

    def set_selected_issue_index(self, y: int) -> None:
        """
        must offset by one since repo indexes starts at 0 and line at 1.
        """
        self.selected_index = y - 1

    def open_repo_in_browser(self) -> None:
        open_in_browser(self.repo.url)

    def open_selected_issue_in_browser(self) -> None:
        if self.has_issues:
            open_in_browser(self.repo[self.selected_index].url)

    def open_repo_in_ranger(self) -> None:
        open_in_ranger(self._address)

    def open_selected_issue_in_lvim_octo(self) -> None:
        if self.has_issues:
            open_in_lvim_octo(self._address, self.repo[self.selected_index].number)

    async def on_click(self, event: events.Click) -> None:
        if event.button == LEFT_BUTTON:
            if event.y == 0:
                self.open_repo_in_browser()
            elif self.is_in_issues_list(event.y):
                self.set_selected_issue_index(event.y)
            else:
                self.open_selected_issue_in_browser()
        if event.button == RIGHT_BUTTON:
            if event.y == 0:
                self.open_repo_in_ranger()
            elif self.is_in_issues_list(event.y):
                self.set_selected_issue_index(event.y)
                self.open_selected_issue_in_lvim_octo()
            else:
                self.open_selected_issue_in_lvim_octo()
        self.refresh()

    async def on_enter(self, _: events.Enter) -> None:
        self.is_selected = True

    async def on_leave(self, _: events.Leave) -> None:
        self.is_selected = False

    def set_selected(self) -> None:
        self.is_selected = True

    def set_not_selected(self) -> None:
        self.is_selected = False


class EZTKView(App):
    WIN_WIDTH = 28
    DEFAULT_WIN_HEIGHT = 29

    repos: Reactive[dict[str, str]] = Reactive({})
    nb_repos: Reactive[int] = Reactive(0)
    repo_views: Reactive[dict[str, RepoView]] = Reactive({})
    selected_repo: Reactive[int] = Reactive(0)
    selected_view: Reactive[RepoView]

    async def on_load(self, _: events.Load) -> None:
        """Bind keys with the app loads (but before entering application mode)"""
        await self.bind("q", "quit", "Quit")
        await self.bind("escape", "quit", "Quit")

        await self.bind("left", "left", "Previous Repo")
        await self.bind("down", "down", "Previous Issue")
        await self.bind("up", "up", "Next Issue")
        await self.bind("right", "right", "Next Repo")

        await self.bind("h", "left", "Previous Repo")
        await self.bind("j", "down", "Previous Issue")
        await self.bind("k", "up", "Next Issue")
        await self.bind("l", "right", "Next Repo")

        await self.bind("f1", "f1", "Open repo in browser")
        await self.bind("f2", "f2", "Open issue in browser")
        await self.bind("f3", "f3", "Open repo in ranger")
        await self.bind("f4", "f4", "Open issue in lvim octo")

    async def on_mount(self, _: events.Mount) -> None:
        self.set_defaults()
        await self.set_grid()

    def set_defaults(self) -> None:
        self.set_repos()
        self.set_repo_views()
        self.set_default_selected_repo()
        self.set_nb_repos()

    def set_repos(self) -> None:
        self.repo_dict = REPOS_DICT

    def set_nb_repos(self) -> None:
        self.nb_repos = len(self.repo_dict)

    def set_default_selected_repo(self) -> None:
        self.selected_repo = 0

    def set_repo_views(self) -> None:
        self.repo_views = {}
        for index, (name, address) in enumerate(self.repo_dict.items()):
            repo_view = RepoView()
            repo_view.set_name(name)
            repo_view.set_address(address)
            repo_view.set_index(index)
            self.repo_views[name] = repo_view

    async def set_grid(self, height=DEFAULT_WIN_HEIGHT) -> None:
        self.grid = await self.view.dock_grid()

        self.grid.add_column("col", fraction=1, max_size=self.WIN_WIDTH)
        self.grid.add_row("row", fraction=1, max_size=height)
        self.grid.set_repeat(True, True)
        self.grid.set_align("center", "center")

        self.grid.place(*self.repo_views.values())

    async def on_resize(self, event: events.Resize) -> None:
        win_height = self.calc_height(event.size.width, event.size.height)
        for row in self.grid.rows:
            row.max_size = win_height
        self.refresh(layout=True)

    def calc_height(self, width: int, height: int) -> int:
        """
        Calculates the height of repo windows.
        """
        return height // math.ceil(self.nb_repos * self.WIN_WIDTH / width) - 1

    def select_view(self, index: int) -> None:
        key = list(self.repo_dict.keys())[index]
        view = self.repo_views[key]
        view.set_selected()
        self.selected_view = view

    def unselect_view(self, index: int) -> None:
        key = list(self.repo_dict.keys())[index]
        view = self.repo_views[key]
        view.set_not_selected()

    async def action_up(self, *_) -> None:
        """select previous issue in current"""
        view = self.selected_view
        if view.has_issues:
            view.selected_index = (view.selected_index - 1) % view.nb_issues
        self.refresh()

    async def action_down(self, *_) -> None:
        """select next issue in current"""
        view = self.selected_view
        if view.has_issues:
            view.selected_index = (view.selected_index + 1) % view.nb_issues
        self.refresh()

    def decr_selected_repo(self) -> None:
        self.selected_repo = (self.selected_repo - 1) % self.nb_repos

    def incr_selected_repo(self) -> None:
        self.selected_repo = (self.selected_repo + 1) % self.nb_repos

    async def action_left(self, *_) -> None:
        """Give focus to previous repo"""
        self.unselect_view(self.selected_repo)
        self.decr_selected_repo()
        self.select_view(self.selected_repo)

    async def action_right(self, *_) -> None:
        """Give focus to next repo"""
        self.unselect_view(self.selected_repo)
        self.incr_selected_repo()
        self.select_view(self.selected_repo)

    async def action_f1(self, *_) -> None:
        self.selected_view.open_repo_in_browser()

    async def action_f2(self, *_) -> None:
        self.selected_view.open_selected_issue_in_browser()

    async def action_f3(self, *_) -> None:
        self.selected_view.open_repo_in_ranger()

    async def action_f4(self, *_) -> None:
        self.selected_view.open_selected_issue_in_lvim_octo()
