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

REPOS_DICT = {
    "cours": "/home/quentin/gdrive/cours/git_cours/cours",
    "cours-nsi": "/home/quentin/gdrive/cours/cours-nsi",
    "imt": "/home/quentin/gdrive/cours/IMT",
    "EcoGestion": "/home/quentin/gdrive/cours/EcoGestion",
    "qkzk": "/home/quentin/gclem/dev/hugo/qkzk",
    "qcm_alchemy": "/home/quentin/gclem/dev/python/boulot_utils/qcm_alchemy",
    "reprographie": "/home/quentin/gclem/dev/python/boulot_utils/reprographie",
    "TSTMG": "/home/quentin/gdrive/cours/TSTMG",
}


class IssueView(Widget):
    style: str

    def on_mount(self) -> None:
        self.style = "grey70"
        self.set_interval(1, self.refresh)

    def render(self) -> Text:
        return Text(
            self.issue.title,
            style=self.style,
            overflow="ellipsis",
            no_wrap=True,
        )

    def set_issue(self, issue: Issue):
        self.issue = issue
        return self

    def set_selected(self):
        self.style = "yellow bold"


class IssueDetail(Widget):
    def on_mount(self):
        self.issue: Issue
        pass

    def set_issue(self, issue: Issue):
        self.issue = issue
        return self

    def render(self) -> Panel:
        return Panel(
            self.issue.body,
            title=self.issue.title,
            subtitle=self.issue.labels_str,
            style="grey100",
            border_style="cyan",
        )


class RepoView(Widget):
    mouse_over: Reactive[bool] = Reactive(False)

    def on_mount(self) -> None:
        self.set_interval(1, self.refresh)
        self.set_interval(30, self.reload_repos)
        self.reload_repos()
        self.selected_index = 0

    def reload_repos(self):
        self.repo = fetch_repo(self._name)

    def render(self) -> Panel:
        content: list[str | IssueView | IssueDetail]
        if len(self.repo) > 0:
            content = [IssueView().set_issue(issue) for issue in self.repo]
            content[self.selected_index].set_selected()
            content.append(IssueDetail().set_issue(self.repo[self.selected_index]))
        else:
            content = [" "]
        return Panel(
            Columns(content),
            title=self._name,
            border_style="red" if self.mouse_over else "blue",
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

    async def on_click(self, event: events.Click) -> None:
        if event.button == 1:
            if event.y == 0:
                open_in_browser(self.repo.url)
            elif self.is_in_issues_list(event.y):
                self.select_issue(event.y)
            else:
                open_in_browser(self.repo[self.selected_index].url)
        if event.button == 3:
            if event.y == 0:
                open_in_ranger(self._address)
            elif self.is_in_issues_list(event.y):
                self.select_issue(event.y)
                open_in_lvim_octo(self._address, self.repo[self.selected_index].number)
            else:
                open_in_lvim_octo(self._address, self.repo[self.selected_index].number)
        self.refresh()

    async def on_enter(self, _: events.Enter) -> None:
        self.mouse_over = True

    async def on_leave(self, _: events.Leave) -> None:
        self.mouse_over = False


class EZTKView(App):
    async def on_load(self, _: events.Load) -> None:
        """Bind keys with the app loads (but before entering application mode)"""
        await self.bind("q", "quit", "Quit")
        await self.bind("escape", "quit", "Quit")

    async def on_mount(self, _: events.Mount) -> None:
        self.set_repos()

        self.repo_views = {}
        for name, address in self.repos_dict.items():
            repo_view = RepoView()
            repo_view.set_name(name)
            repo_view.set_address(address)
            self.repo_views[name] = repo_view
        await self.set_grid()

    async def set_grid(self, height=29):
        self.grid = await self.view.dock_grid()

        self.grid.add_column("col", fraction=1, max_size=28)
        self.grid.add_row("row", fraction=1, max_size=height)
        self.grid.set_repeat(True, True)
        self.grid.set_align("stretch", "center")

        self.grid.place(*self.repo_views.values())

    async def on_resize(self, event: events.Resize) -> None:
        self.log(f"New size : {event.size}")
        new_width = event.size.width
        if new_width < 110:
            new_height = 14
        elif new_width < 230:
            new_height = 28
        else:
            new_height = 56
        for row in self.grid.rows:
            row.max_size = new_height
        self.refresh(layout=True)

    def set_repos(self) -> None:
        self.repos_dict = REPOS_DICT
