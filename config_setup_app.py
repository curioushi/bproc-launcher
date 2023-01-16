import os
import os.path as osp
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Button, Static, Label, Input, Tree, TreeNode
from textual import log
import omegaconf
from omegaconf import OmegaConf
from typing import List


class AppHeader(Static):

    def compose(self) -> ComposeResult:
        self.update("Configuration Setup")
        return super().compose()


class OptionsView(Vertical):
    pass


class OptionLayout(Horizontal):
    pass


class OptionsTree(Tree):
    def __init__(self, label, data=None, name=None, id=None, classes=None) -> None:
        super().__init__(label, data, name=name, id=id, classes=classes)
        self.show_root = True
        self.auto_expand = False


class Submit(Button):
    pass


class SaveAsDefault(Button):
    pass


class ConfigSetupApp(App):
    CSS_PATH = 'config_setup_app.css'
    EXCLUDE_PATHS = [
        ['CC_TEXTURES_DIR'],
        ['OUTPUT_DIR'],
        ['ENABLE_DEPTH'],
        ['OBJECT', 'FILE'],
        ['OBJECT', 'SHADING_MODE'],
        ['OBJECT', 'UNIT']
    ]

    def __init__(self, config=None, driver_class=None, css_path=None, watch_css=False):
        super().__init__(driver_class, css_path, watch_css)
        # self.config = OmegaConf.load("config.yaml")
        self.config = config

    def on_tree_node_selected(self, event):
        options_view = self.query_one("OptionsView")
        while len(options_view.children) > 0:
            last = options_view.children[-1]
            last.remove()
        node = event.node

        if len(node._children) == 0:
            node = node._parent

        path = []
        path.append(str(node._label))
        parent = node._parent
        while parent:
            path = [str(parent._label)] + path
            parent = parent._parent
        path = path[1:]

        for child in node._children:
            if len(child._children) == 0:
                cfg = self.config
                for key in path:
                    cfg = cfg[key]
                label = str(child._label)
                value = cfg[label]
                input_widget = Input()
                input_widget.path = path + [label]
                input_widget.value = str(value)
                options_view.mount(OptionLayout(
                    Label(child._label), input_widget))

    def on_button_pressed(self, event):
        button = event.button
        if button.id == "submit":
            self.exit(self.config)
        elif button.id == "save_as_default":
            default_config = osp.join(osp.abspath(osp.dirname(__file__)), "config.yaml")
            with open(default_config, 'w') as f:
                OmegaConf.save(config=self.config, f=f.name)

    def on_input_changed(self, event):
        input_widget = event.input
        path = input_widget.path
        cfg = self.config
        for key in path[:-1]:
            cfg = cfg[key]

        try:
            cfg[path[-1]] = eval(input_widget.value)
        except:
            cfg[path[-1]] = str(input_widget.value)

    def compose(self) -> ComposeResult:
        tree = OptionsTree("")
        tree.root.expand()

        def build_tree_recursively(node: TreeNode, config_dict, path: List[str]):
            if config_dict:
                for k, v in config_dict.items():
                    if isinstance(v, omegaconf.dictconfig.DictConfig):
                        subnode = node.add(k, expand=True)
                        build_tree_recursively(subnode, v, path + [k])
                    else:
                        if path + [k] not in self.EXCLUDE_PATHS:
                            node.add_leaf(k)

        build_tree_recursively(tree.root, self.config, [])
        self.options_view = OptionsView()

        yield Vertical(
            OptionLayout(AppHeader(),
                         SaveAsDefault("SaveAsDefault", id='save_as_default'),
                         Submit("Submit", id='submit')),
            Horizontal(
                tree, self.options_view
            ))


if __name__ == '__main__':
    cfg = OmegaConf.load("config.yaml")
    app = ConfigSetupApp(config=cfg)
    result = app.run()
    print(result)
