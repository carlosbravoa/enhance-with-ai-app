import gi
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio
from enhance_with_ai.window import MainWindow

class EnhanceWithAIApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="enhance-with-ai-openai",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

    def do_activate(self):
        win = MainWindow(self)
        win.present()

if __name__ == "__main__":
    main()

def main():
    app = EnhanceWithAIApp()
    app.run()
