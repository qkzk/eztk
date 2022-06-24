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


class IssueView(Widget):
    is_repo_selected: Reactive[bool] = Reactive(False)
    text_color: Reactive[str] = Reactive("grey70")

    def on_mount(self) -> None:
        self.text_color = "grey70"
        self.set_interval(1, self.refresh)
        self.is_repo_selected = False
        self.selected_color: str

    def render(self) -> Text:
        return Text(
            self.issue.title,
            style=self.text_color,
            overflow="ellipsis",
            no_wrap=True,
        )

    def set_issue(self, issue: Issue):
        self.issue = issue
        return self

    def set_selected(self):
        self.text_color = self.selected_color + " bold italic"

    def set_repo_selected(self):
        self.is_repo_selected = True
        self.text_color = "grey70 bold"

    def set_repo_not_selected(self):
        self.is_repo_selected = False
        self.text_color = "grey70"

    def set_selected_color(self, color):
        self.selected_color = color
        return self


class IssueDetail(Widget):
    is_repo_selected: Reactive[bool] = Reactive(False)

    def on_mount(self):
        self.issue: Issue
        self.border_style: str

    def set_issue(self, issue: Issue):
        self.issue = issue
        return self

    def render(self) -> Panel:
        return Panel(
            self.issue.body,
            title=self.issue.title,
            subtitle=self.issue.labels_str,
            style="grey100 bold" if self.is_repo_selected else "grey100",
            border_style=self.border_style,
        )

    def set_repo_selected(self):
        self.is_repo_selected = True

    def set_repo_not_selected(self):
        self.is_repo_selected = False

    def set_color(self, color):
        self.border_style = color
        return self


class RepoView(Widget):
    is_selected: Reactive[bool] = Reactive(False)

    def on_mount(self) -> None:
        self.set_interval(1, self.refresh)
        self.set_interval(30, self.reload_repos)
        self.reload_repos()
        self.selected_index = 0
        self.is_selected = False
        self.nb_issues = 0
        self.has_issues = False
        self.index: int
        self.border_style: str

    def set_index(self, index):
        self.index = index
        self.border_style = self.calc_border_style()

    def reload_repos(self):
        self.repo = fetch_repo(self._name)

    def calc_border_style(self):
        style = f"{COLORS[self.index % len(COLORS)]}"
        return style

    def render(self) -> Panel:
        content: list[str | IssueView | IssueDetail]
        self.nb_issues = len(self.repo)
        if len(self.repo) > 0:
            self.has_issues = True
            content = [
                IssueView().set_issue(issue).set_selected_color(self.border_style)
                for issue in self.repo
            ]
            content.append(
                IssueDetail()
                .set_issue(self.repo[self.selected_index])
                .set_color(self.border_style)
            )
            if self.is_selected:
                for view in content:
                    view.set_repo_selected()
            content[self.selected_index].set_selected()
        else:
            content = [" "]
            self.has_issues = False
        border_style = (
            self.border_style + " bold italic"
            if self.is_selected
            else self.border_style
        )
        return Panel(
            Columns(content),
            title=self._name,
            border_style=border_style,
        )

    def set_name(self, name: str) -> None:
        self._name = name

    def set_address(self, address: str) -> None:
        self._address = address

    def is_in_issues_list(self, y: int) -> bool:
        return len(self.repo) > 1 and y <= len(self.repo)

    def select_issue(self, y: int):
        """
        must offset by one since repo indexes starts at 0 and line at 1.
        """
        self.selected_index = y - 1

    def open_repo_in_browser(self):
        open_in_browser(self.repo.url)

    def open_selected_issue_in_browser(self):
        open_in_browser(self.repo[self.selected_index].url)

    def open_repo_in_ranger(self):
        open_in_ranger(self._address)

    def open_selected_issue_in_lvim_octo(self):
        open_in_lvim_octo(self._address, self.repo[self.selected_index].number)

    async def on_click(self, event: events.Click) -> None:
        if event.button == 1:
            if event.y == 0:
                self.open_repo_in_browser()
            elif self.is_in_issues_list(event.y):
                self.select_issue(event.y)
            else:
                self.open_selected_issue_in_browser()
        if event.button == 3:
            if event.y == 0:
                self.open_repo_in_ranger()
            elif self.is_in_issues_list(event.y):
                self.select_issue(event.y)
                self.open_selected_issue_in_lvim_octo()
            else:
                self.open_selected_issue_in_lvim_octo()
        self.refresh()

    async def on_enter(self, _: events.Enter) -> None:
        self.is_selected = True

    async def on_leave(self, _: events.Leave) -> None:
        self.is_selected = False

    def set_selected(self):
        self.is_selected = True

    def set_not_selected(self):
        self.is_selected = False


class EZTKView(App):
    WIN_WIDTH = 28

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
        self.set_repos()

        self.repo_views: dict[str, RepoView] = {}
        for index, (name, address) in enumerate(self.repo_dict.items()):
            repo_view = RepoView()
            repo_view.set_name(name)
            repo_view.set_address(address)
            repo_view.set_index(index)
            self.repo_views[name] = repo_view
        await self.set_grid()

    async def set_grid(self, height=29):
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

    def set_repos(self) -> None:
        self.repo_dict = REPOS_DICT
        self.nb_repos = len(self.repo_dict)
        self.selected_repo = 0

    def calc_height(self, width: int, height) -> int:
        """
        Calculates the height of repo windows.
        """
        max_win_per_row = width / self.WIN_WIDTH
        if max_win_per_row >= self.nb_repos:
            win_height = height - 1
        elif max_win_per_row >= math.ceil(self.nb_repos / 2):
            win_height = (height // 2) - 1
        elif max_win_per_row >= math.ceil(self.nb_repos / 3):
            win_height = (height // 3) - 1
        else:
            win_height = (height // 4) - 1
        return win_height

    def get_selected_view(self) -> RepoView:
        key = list(self.repo_dict.keys())[self.selected_repo]
        return self.repo_views[key]

    def set_selected_repo(self, index: int):
        key = list(self.repo_dict.keys())[index]
        view = self.repo_views[key]
        view.set_selected()

    def set_not_selected_repo(self, index: int):
        key = list(self.repo_dict.keys())[index]
        view = self.repo_views[key]
        view.set_not_selected()

    async def action_up(self, *_) -> None:
        """select previous issue in current"""
        view = self.get_selected_view()
        if view.has_issues:
            view.selected_index = (view.selected_index - 1) % view.nb_issues
        self.refresh()

    async def action_down(self, *_) -> None:
        """select next issue in current"""
        view = self.get_selected_view()
        if view.has_issues:
            view.selected_index = (view.selected_index + 1) % view.nb_issues
        self.refresh()

    async def action_left(self, *_) -> None:
        """Give focus to previous repo"""
        self.set_not_selected_repo(self.selected_repo)
        self.selected_repo = (self.selected_repo - 1) % self.nb_repos
        self.set_selected_repo(self.selected_repo)

    async def action_right(self, *_) -> None:
        """Give focus to next repo"""
        self.set_not_selected_repo(self.selected_repo)
        self.selected_repo = (self.selected_repo + 1) % self.nb_repos
        self.set_selected_repo(self.selected_repo)

    async def action_f1(self, *_) -> None:
        self.get_selected_view().open_repo_in_browser()

    async def action_f2(self, *_) -> None:
        self.get_selected_view().open_selected_issue_in_browser()

    async def action_f3(self, *_) -> None:
        self.get_selected_view().open_repo_in_ranger()

    async def action_f4(self, *_) -> None:
        self.get_selected_view().open_selected_issue_in_lvim_octo()
