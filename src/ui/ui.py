from __future__ import annotations
import math

from rich.box import SQUARE, HEAVY, Box, HORIZONTALS
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

HELP_MESSAGE = """
EZTK

Display your github issues in the terminal.

← →: change repo 
 ↓ ↑: change issue

h l: change repo
 j k: change issue


  F1: open repo in browser
   F2: open issue in browser
 F3: open repo in ranger
F4: open issue in Octo

p: toggle Help
"""
HELP_SIZE = len(HELP_MESSAGE.splitlines()) + 6


class IssueView(Widget):
    """
    Represent a line of text with a issue name
    Displayed in the `RepoView`.
    """

    is_repo_selected: Reactive[bool] = Reactive(False)
    # text_color: Reactive[str] = Reactive("grey50")
    selected_issue_color: Reactive[str]

    def on_mount(self) -> None:
        """Every second, refresh the view"""
        self.set_interval(1, self.refresh)

    def render(self) -> Text:
        """
        Called when rendering the view.
        Returns a single line with the name.
        Bright + italic if the issue issue is selected.
        """
        return Text(
            self.title,
            style=self.text_color,
            overflow="ellipsis",
            no_wrap=True,
        )

    @property
    def title(self) -> str:
        """
        Returns a title of the `Issue`.
        Returns an empty string if the Issue isn't set.
        """
        try:
            return self.issue.title if self.issue.title else ""
        except AttributeError:
            return ""

    def with_issue(self, issue: Issue) -> "IssueView":
        """Set the issue, returns itself"""
        self.issue = issue
        return self

    def with_selected_color(self, color: str) -> "IssueView":
        """Set the selected color, returns itself."""
        self.selected_issue_color = color
        self.text_color = color
        return self

    def set_selected(self) -> None:
        """Set the color to italic and bright"""
        self.text_color = "white bold"

    def set_repo_selected(self) -> None:
        """When the repo is selected by the user, use brighter colors."""
        pass


class IssueDetail(Widget):
    """The detailed view of the issue."""

    is_repo_selected: Reactive[bool] = Reactive(False)
    border_style: Reactive[str]
    issue: Reactive[Issue]

    def with_issue(self, issue: Issue) -> "IssueDetail":
        """Set the issue and returns itself."""
        self.issue = issue
        return self

    def with_border_style(self, color: str) -> "IssueDetail":
        """Set the border style and returns itselfs"""
        self.border_style = color
        return self

    def with_selection(self, is_parent_selected: bool) -> "IssueDetail":
        """Set the selection status and returns itself."""
        if is_parent_selected:
            self.is_repo_selected = True
        return self

    @property
    def box(self) -> Box:
        """The square box around the issue view. Bold when issue is selected."""
        return HEAVY if self.is_repo_selected else HORIZONTALS

    def render(self) -> Panel:
        return Panel(
            self.issue.body if self.issue.body else "",
            title=self.issue.title if self.issue.title else "",
            subtitle=self.issue.labels_str,
            style=self.color,
            border_style=self.border_style,
            box=self.box,
        )

    @property
    def color(self) -> str:
        """Set the color. Use bold if the repo is selected."""
        return "grey100 bold" if self.is_repo_selected else "grey100"

    def set_repo_selected(self) -> None:
        """Set itself as selected"""
        self.is_repo_selected = True

    def set_selected(self):
        pass


class HelpView(Widget):
    """Static view of the help."""

    def render(self):
        """Called when rendering."""
        return Panel(
            Text(HELP_MESSAGE, justify="center"),
            box=HEAVY,
            border_style="bold cyan",
            subtitle="EZTK Help",
            title="EZTK",
            style="bold cyan",
            highlight=True,
            padding=(1, 1),
        )


class RepoView(Widget):
    """
    The view of the repository.
    """

    is_selected: Reactive[bool] = Reactive(False)
    nb_issues: Reactive[int] = Reactive(0)
    selected_index: Reactive[int] = Reactive(0)
    has_issues: Reactive[bool] = Reactive(False)
    index: Reactive[int]

    async def on_mount(self) -> None:
        """
        Set the timers (every second redraw, every 30 seconds fetch the repo)
        Load the repos.
        """
        self.set_interval(1, self.refresh)
        self.set_interval(30, self.reload_repo)
        self.reload_repo()

    def with_attributes(self, name: str, address: str, index: int) -> "RepoView":
        """Set the attributes and returns itself."""
        self._name = name
        self._address = address
        self.index = index
        return self

    def reload_repo(self) -> None:
        """
        Fetch the repos.
        Since the `Repo` object inherit from `list`, we can set it to an empty `list`
        when the request returns `None` (ie. when `requests` encountered a connexion error.)
        """
        response = fetch_repo(self._name)
        if response is not None:
            self.repo = response
        else:
            self.repo = []

    def count_issues(self):
        """Set `nb_issues` and `has_issues` attributes."""
        self.nb_issues = len(self.repo)
        self.has_issues = self.nb_issues != 0

    def generate_content(self) -> list[IssueView | IssueDetail]:
        """
        Generate the view content.
        Returns a list of `ViewIssue` and `ViewDetail` if there's opened issues, else `[" "]`.
        Set the selected issue as 'selected'.
        Give them the propor color.
        """
        self.count_issues()
        if not self.has_issues:
            return []

        content: list[IssueView | IssueDetail] = [
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
        """Set the child issues as selected when user selected this repo."""
        for view in content:
            view.set_repo_selected()

    def generate_issue_detail(self) -> IssueDetail:
        """Generate the issue detail of selected issue."""
        return (
            IssueDetail()
            .with_issue(self.repo[self.selected_index])
            .with_border_style(self.border_style)
            .with_selection(self.is_selected)
        )

    @property
    def border_style(self) -> str:
        """
        Set the border style to its color.
        It's also bold and italic when the user selected the issue.
        """
        return f"{COLORS[self.index % len(COLORS)]}" + (
            " bold italic" if self.is_selected else ""
        )

    @property
    def box(self) -> Box:
        """The type of border. thin square when not selected, bold when it is."""
        return HEAVY if self.is_selected else HORIZONTALS

    def render(self) -> Panel:
        """
        Render the repo view.
        A simple `Panel` with a few columns.
        Color and border styles depend on the status (selected or not).
        Generate the content every frame.
        """
        return Panel(
            Columns(self.generate_content()),
            title=self._name,
            border_style=self.border_style,
            box=self.box,
        )

    def is_in_issues_list(self, y: int) -> bool:
        """True if the line is a valid index for an issue."""
        return self.has_issues and y <= len(self.repo)

    def set_selected_issue_index(self, y: int) -> None:
        """
        must offset by one since repo indexes starts at 0 and line at 1.
        """
        self.selected_index = y - 1

    def open_repo_in_browser(self) -> None:
        """Open the repo web url in browser"""
        open_in_browser(self.repo.url)

    def open_selected_issue_in_browser(self) -> None:
        """Open the selected issue url web url in browser"""
        if self.has_issues:
            open_in_browser(self.repo[self.selected_index].url)

    def open_repo_in_ranger(self) -> None:
        """Open the repo local address in ranger."""
        open_in_ranger(self._address)

    def open_selected_issue_in_lvim_octo(self) -> None:
        """Open the issue in nvim octo"""
        if self.has_issues:
            open_in_lvim_octo(self._address, self.repo[self.selected_index].number)

    async def on_click(self, event: events.Click) -> None:
        """
        Callback when a RepoView is clicked
        Inform main view of selection.
        Left click : open in browser or selection of issue.
        Right click : open locally and selection of issue.
        """
        self.inform_boss_view_of_selection()
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

    @property
    def boss_view(self) -> EZTKView:
        """Returns the parent view. ie. the main view."""
        return self.parent.parent.parent

    def inform_boss_view_of_selection(self) -> None:
        """Message the main view of self selection."""
        self.boss_view.set_selected_widget(self.index)

    async def on_enter(self, _: events.Enter) -> None:
        """
        Callback when entering the view.
        Inform parent of selection.
        set self as selected.
        """
        self.inform_boss_view_of_selection()
        self.is_selected = True

    async def on_leave(self, _: events.Leave) -> None:
        """
        Callback when leaving the view.
        set self as not selected.
        """
        self.is_selected = False

    def set_selected(self) -> None:
        """
        set self as selected.
        """
        self.is_selected = True

    def set_not_selected(self) -> None:
        """
        set self as not selected.
        """
        self.is_selected = False


class EZTKView(App):
    """
    Main entry point of the application.

    Holds a list of children views :
    * grid of repo views
    * single bar with help.

    Reponsible for keystrokes interactions.
    Set the selection of repo views and issues.
    """

    WIN_WIDTH = 28
    DEFAULT_WIN_HEIGHT = 29

    repos: Reactive[dict[str, str]] = Reactive({})
    nb_repos: Reactive[int] = Reactive(0)
    repo_views: Reactive[dict[str, RepoView]] = Reactive({})
    selected_repo: Reactive[int] = Reactive(0)
    selected_view: Reactive[RepoView]
    help_displayed: Reactive[bool] = Reactive(False)

    async def on_load(self, _: events.Load) -> None:
        """Bind keys with the app loads (but before entering application mode)"""
        await self.bind("q", "quit", "Quit")
        await self.bind("escape", "quit", "Quit")

        await self.bind("p", "help", "Help toggle")

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

    async def on_key(self, key: events.Key):
        """
        default callback when a key is pressed.
        if the keys isn't binded, open the help.
        """
        if key.key not in self.bindings.keys:
            self.help_displayed = not self.help_displayed

    async def on_mount(self, _: events.Mount) -> None:
        """
        Callback when the view is ready.
        Set the defaults (repos, parameters),
        Set the help bar,
        Set the grid view.
        """
        self.set_defaults()
        await self.set_bar()
        await self.set_grid()

        self.bar.layout_offset_y = -HELP_SIZE

    def watch_help_displayed(self, help_displayed: bool) -> None:
        """Called when `help_displayed` changes."""
        self.bar.animate("layout_offset_y", 0 if help_displayed else -HELP_SIZE)

    async def set_bar(self) -> None:
        """
        Set the help bar view as top, hidden, above other views.
        """
        self.bar = HelpView()
        await self.view.dock(self.bar, edge="top", size=HELP_SIZE, z=1)

    def set_defaults(self) -> None:
        """
        Set default parameters :
        * dict of repos + addresses,
        * dict views,
        * number of reposes,
        * select the first one.
        """
        self.set_repos()
        self.set_repo_views()
        self.set_repo_names()
        self.set_default_selected_repo()
        self.set_nb_repos()
        self.select_view(self.selected_repo)

    def set_repos(self) -> None:
        """
        Load the repos from config file.
        """
        self.repo_dict = REPOS_DICT

    def set_nb_repos(self) -> None:
        """
        Count the repos.
        """
        self.nb_repos = len(self.repo_dict)

    def set_default_selected_repo(self) -> None:
        """
        Set the selected index to 0
        """
        self.selected_repo = 0

    def set_selected_widget(self, index: int) -> None:
        """
        Select the first widget.
        """
        self.unselect_view(self.selected_repo)
        self.selected_repo = index
        self.select_view(self.selected_repo)

    def set_repo_views(self) -> None:
        """
        Creates the dict of `str: RepoView` with their attributes.
        """
        self.repo_views = {
            name: RepoView().with_attributes(name=name, address=address, index=index)
            for index, (name, address) in enumerate(self.repo_dict.items())
        }

    def set_repo_names(self) -> None:
        """
        Creates a list of repo names.
        """
        self.repo_names = list(self.repo_dict)

    async def set_grid(self, height=DEFAULT_WIN_HEIGHT) -> None:
        """
        Setup the grid layout.
        Called twice when entering the app.
        First call (default parameters) has no idea of size.
        Then `on_resize` is called, and this fuction is called again with proper size.

        TODO: simplify that
        """
        self.grid = await self.view.dock_grid()

        self.grid.add_column("col", fraction=1, max_size=self.WIN_WIDTH)
        self.grid.add_row("row", fraction=1, max_size=height)
        self.grid.set_repeat(True, True)
        self.grid.set_align("center", "center")

        self.grid.place(*self.repo_views.values())

    async def on_resize(self, event: events.Resize) -> None:
        """
        Callback when a resize event occurs.
        Set the size, force the redraw of layout.

        1. Calc the corresponding size for every repoview.
        2. Set the corresponding size of every child in grid.
        3. Force a recalc of the layout.
        """
        win_height = self.calc_height(event.size.width, event.size.height)
        for row in self.grid.rows:
            row.max_size = win_height
        self.refresh(layout=True)

    def calc_height(self, width: int, height: int) -> int:
        """
        Calculates the height of repo windows.
        """
        return height // math.ceil(self.nb_repos * self.WIN_WIDTH / width) - 1

    def get_view_per_index(self, index: int) -> RepoView:
        """
        Returns a `RepoView` from its index.
        """
        return self.repo_views[self.repo_names[index]]

    def select_view(self, index: int) -> None:
        """
        Select a repo view by its index.
        """
        view = self.get_view_per_index(index)
        view.set_selected()
        self.selected_view = view

    def unselect_view(self, index: int) -> None:
        """
        Unselect a repo view by its index.
        """
        view = self.get_view_per_index(index)
        view.set_not_selected()

    async def action_up(self, *_) -> None:
        """select previous issue in current selected repo"""
        view = self.selected_view
        if view.has_issues:
            view.selected_index = (view.selected_index - 1) % view.nb_issues
        self.refresh()

    async def action_down(self, *_) -> None:
        """select next issue in current selected repo"""
        view = self.selected_view
        if view.has_issues:
            view.selected_index = (view.selected_index + 1) % view.nb_issues
        self.refresh()

    def decr_selected_repo(self) -> None:
        """Decrement selected index. Cycle through if negavite"""
        self.selected_repo = (self.selected_repo - 1) % self.nb_repos

    def incr_selected_repo(self) -> None:
        """Increment selected index. Cycle through if overflow."""
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
        """Callback when F1 is pressed. Open repo in browser"""
        self.selected_view.open_repo_in_browser()

    async def action_f2(self, *_) -> None:
        """Callback when F1 is pressed. Open issue in browser"""
        self.selected_view.open_selected_issue_in_browser()

    async def action_f3(self, *_) -> None:
        """Callback when F3 is pressed. Open repo in ranger"""
        self.selected_view.open_repo_in_ranger()

    async def action_f4(self, *_) -> None:
        """Callback when F1 is pressed. Open issue in nvim octo"""
        self.selected_view.open_selected_issue_in_lvim_octo()

    async def action_help(self, *_) -> None:
        """Callback when E is pressed. Toggle help"""
        self.help_displayed = not self.help_displayed
