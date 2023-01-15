from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Button, Footer, Static, Label, Input, Checkbox, ListItem, ListView, Tree, TreeNode
from textual import log


class AppHeader(Static):
    def compose(self):
        self.update("Configuration Setup")


class MyVertical(Vertical):
    pass


class MyHorizontal(Horizontal):
    pass


class ConfigSetupApp(App):
    CSS_PATH = 'config_setup_app.css'

    def compose(self) -> ComposeResult:
        yield Vertical(
            MyHorizontal(AppHeader(),
                         Button("Submit")),
            Horizontal(
                Tree("Tree"),
                MyVertical(
                    MyHorizontal(Label("Param1"), Input()),
                    MyHorizontal(Label("Param2"), Input()),
                    MyHorizontal(Label("Param1"), Input()),
                    MyHorizontal(Label("Param2"), Input()),
                    MyHorizontal(Label("Param1"), Input()),
                    MyHorizontal(Label("Param2"), Input()),
                    MyHorizontal(Label("Param1"), Input()),
                    MyHorizontal(Label("Param2"), Input()),
                    MyHorizontal(Label("Param1"), Input()),
                    MyHorizontal(Label("Param2"), Input()),
                    MyHorizontal(Label("Param1"), Input()),
                    MyHorizontal(Label("Param2"), Input()),
                    MyHorizontal(Label("Param1"), Input()),
                    MyHorizontal(Label("Param2"), Input()),
                )
            ))


if __name__ == '__main__':
    app = ConfigSetupApp()
    app.run()
