from gi.repository import Caja, GObject
import subprocess
import urllib.parse
import os


def _uri_to_path(uri: str) -> str:
    if not uri or not uri.startswith("file://"):
        return ""
    path = uri[7:]
    if path.startswith("localhost"):
        path = path[len("localhost"):]
    if not path.startswith("/"):
        path = "/" + path
    return urllib.parse.unquote(path)


def _run_action(action: str, paths: list[str]) -> None:
    try:
        cmd = ["ydmenu-py-env", action]
        if paths:
            cmd.extend(paths)
        subprocess.Popen(cmd)
    except Exception:
        here = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.abspath(os.path.join(here, os.pardir, os.pardir))
        wrapper = os.path.join(repo_root, "ydmenu-py-env")
        if os.path.exists(wrapper) and os.access(wrapper, os.X_OK):
            cmd = [wrapper, action]
            if paths:
                cmd.extend(paths)
            subprocess.Popen(cmd)


class YaDiskCajaExtension(GObject.GObject, Caja.MenuProvider):
    def _collect_paths(self, files) -> list[str]:
        paths: list[str] = []
        if not files:
            return paths
        for f in files:
            try:
                uri = f.get_uri()
                p = _uri_to_path(uri)
                if p:
                    paths.append(p)
            except Exception:
                pass
        return paths

    def _build_submenu(self, files) -> Caja.MenuItem:
        submenu = Caja.Menu()

        actions = [
            ("Publish (COM)", "PublishToYandexCom"),
            ("Publish (RU)", "PublishToYandex"),
            ("Unpublish", "UnpublishFromYandex"),
            ("Unpublish All Copies", "UnpublishAllCopy"),
            ("Save Clipboard", "ClipboardToStream"),
            ("Save & Publish Clipboard (COM)", "ClipboardPublishToCom"),
            ("Save & Publish Clipboard (RU)", "ClipboardPublish"),
            ("Copy to Stream", "FileAddToStream"),
            ("Move to Stream", "FileMoveToStream"),
        ]

        paths = self._collect_paths(files)

        def make_activate(act: str):
            return lambda _mi, _p=paths: _run_action(act, _p)

        for label, act in actions:
            item = Caja.MenuItem(name=f"YaDisk::{act}", label=f"YaDisk – {label}")
            item.connect('activate', make_activate(act))
            submenu.append_item(item)

        top = Caja.MenuItem(name="YaDisk::Top", label="YaDisk")
        top.set_submenu(submenu)
        return top

    def get_background_items(self, _window, _file):
        return [self._build_submenu([])]

    def get_file_items(self, _window, files):
        return [self._build_submenu(files)]


