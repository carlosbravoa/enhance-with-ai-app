import gi
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio
from .window import MainWindow

class EnhanceWithAIApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="cl.cabra.EnhanceWithAI",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

    def do_activate(self):
        win = MainWindow(self)
        win.present()
