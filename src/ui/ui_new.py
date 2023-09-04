from textual.app import App, ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.geometry import Size
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, Label, Markdown, Static

from ..model import Issue

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
    """A repository widget."""

    def __init__(self, a: int):
        super().__init__()
        self.a = a

    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""
        yield Label(str(self.a), id="repo")
        yield IssueView(self.a * 2)
        yield IssueView(self.a * 2 + 1)


class IssueView(Static):
    dev_text = reactive("")

    def __init__(self, b: int):
        super().__init__()
        self.b = b

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        if event.button.id == "title":
            self.__toggle_content()
        elif event.button.id == "edit":
            self.__edit()
        elif event.button.id == "close":
            self.__close()

    def __toggle_content(self):
        # self.toggle_class("empty")
        # self.toggle_class("full")
        content = self.query_one(Markdown)
        self.dev_text = DEV_TEXT
        content.update(self.dev_text)
        content.toggle_class("display")
        content.toggle_class("none")
        self.update()

    def get_content_height(self, container: Size, viewport: Size, a) -> int:
        """Force content width size."""
        return 1

    def __edit(self):
        pass

    def __close(self):
        pass

    def on_mount(self):
        # self.add_class("empty")
        pass

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal():
                yield Button(str(self.b), id="title", variant="success")
                yield Button("Edit", id="edit", variant="warning")
                yield Button("Close", id="close", variant="error")
            yield Markdown(self.dev_text, classes="none")


class EZView(App):
    """A Textual app to manage stopwatches."""

    TITLE = "EZTK"
    CSS_PATH = "ui.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"), ("q", "quit", "quit")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield ScrollableContainer(*(RepoView(i) for i in range(10)))

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark
