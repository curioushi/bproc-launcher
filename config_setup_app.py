from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Button, Header, Footer, Static, Label, Input, Checkbox, ListItem, ListView, Tree, TreeNode
from textual import log


class MyHeader(Static):
    def on_mount(self) -> None:
        self.update('Configuration Setup')

class ConfigSetupApp(App):

    CSS_PATH = 'config_setup_app.css'

    def on_button_pressed(self):
        log.debug('my button mouse down')

    def on_click(self):
        log.debug('clicked')

    def on_tree_node_selected(self, event):
        print('node')
        node: TreeNode = event.node
        log.debug(node._label)
        print('node')


    def compose(self) -> ComposeResult:
        tree: Tree[dict] = Tree("")
        tree.root.expand()
        characters = tree.root.add("Characters", expand=True)
        characters.add_leaf("Paul")
        characters.add_leaf("Jessica")
        characters.add_leaf("Chani")
        yield Horizontal(tree, 
                         Container(MyHeader(),
                                   Label("CC_TEXTURES_DIR"), Input(),
                                   Label("ENABLE_DEPTH"), Checkbox(),
                                   Label("SHADING_MODE"), ListView(
                             ListItem(Static("auto")),
                             ListItem(Static("smooth")),
                             ListItem(Static("flat"))),
                             Button(), classes='option')
                         )


if __name__ == '__main__':
    app = ConfigSetupApp()
    app.run()
