import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib, Gdk
from .config import load_config, ConfigError
from .openai_client import OpenAIClient
import threading


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)

        self.set_title("Enhance With AI")
        self.set_default_size(900, 650)

        self.cancel_stream = False
        self.auto_scroll = True
        self.sending = False
        self.client = None

        self.prompt_options = [
            "Summarize",
            "Explain",
            "Enhance",
            "Proofread",
            "Write your own prompt"
        ]

        self._setup_css()
        self._build_ui()
        self._load_config()

        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key_controller)

    # -------------------------------------------------
    # CSS
    # -------------------------------------------------
    def _setup_css(self):
        css = """
        .text-view-frame {
            background-color: @theme_base_color;
            border-radius: 12px;
            border: 1px solid @borders;
        }

        .text-view-frame textview {
            padding: 12px;
        }

        .section-title {
            font-weight: bold;
            opacity: 0.85;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    # -------------------------------------------------
    # UI
    # -------------------------------------------------
    def _build_ui(self):
        # Header bar (minimal, clean)
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Enhance With AI"))

        self.spinner = Gtk.Spinner()
        header.pack_end(self.spinner)

        # Prompt selector
        self.prompt_dropdown = Gtk.DropDown.new_from_strings(self.prompt_options)
        self.prompt_dropdown.connect("notify::selected", self.on_prompt_changed)

        self.custom_prompt_entry = Gtk.Entry()
        self.custom_prompt_entry.set_placeholder_text("Write your instruction…")
        self.custom_prompt_entry.set_visible(False)

        prompt_row = Gtk.Box(spacing=12)
        prompt_label = Gtk.Label(label="Instruction")
        prompt_label.set_size_request(100, -1)
        prompt_label.set_halign(Gtk.Align.START)

        prompt_row.append(prompt_label)
        prompt_row.append(self.prompt_dropdown)

        prompt_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=6
        )
        prompt_box.append(prompt_row)
        prompt_box.append(self.custom_prompt_entry)

        # Input
        input_label = self._section_label("Input")

        self.input_view = Gtk.TextView(
            wrap_mode=Gtk.WrapMode.WORD_CHAR
        )
        #self.input_view.set_placeholder_text(
        #    "Paste or type text to enhance…"
        #)

        input_scroll = Gtk.ScrolledWindow(vexpand=True)
        input_scroll.set_child(self.input_view)
        input_scroll.add_css_class("text-view-frame")

        # Output
        output_label = self._section_label("Output")

        self.output_view = Gtk.TextView(
            editable=False,
            wrap_mode=Gtk.WrapMode.WORD_CHAR
        )
        self.output_view.set_cursor_visible(False)
        #self.output_view.set_placeholder_text(
        #    "AI responses will appear here…"
        #)

        output_scroll = Gtk.ScrolledWindow(vexpand=True)
        output_scroll.set_child(self.output_view)
        output_scroll.add_css_class("text-view-frame")

        # Buttons
        self.send_btn = Gtk.Button(label="Send")
        self.send_btn.add_css_class("suggested-action")
        self.send_btn.connect("clicked", self.on_send)

        self.clear_btn = Gtk.Button(label="Clear")
        self.clear_btn.connect("clicked", self.on_clear)

        paste_btn = Gtk.Button(
            label="Paste",
            icon_name="edit-paste-symbolic"
        )
        paste_btn.connect("clicked", self.on_paste_clipboard)

        self.stop_btn = Gtk.Button(
            label="Stop",
            icon_name="media-playback-stop-symbolic"
        )
        self.stop_btn.add_css_class("destructive-action")
        self.stop_btn.set_sensitive(False)
        self.stop_btn.connect("clicked", self.on_stop)

        button_box = Gtk.Box(
            spacing=6,
            halign=Gtk.Align.END
        )
        button_box.append(paste_btn)
        button_box.append(self.clear_btn)
        button_box.append(self.stop_btn)
        button_box.append(self.send_btn)

        # Main content
        content = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
            margin_top=12,
            margin_bottom=12,
            margin_start=12,
            margin_end=12,
        )

        content.append(prompt_box)
        content.append(input_label)
        content.append(input_scroll)
        content.append(button_box)
        content.append(output_label)
        content.append(output_scroll)

        clamp = Adw.Clamp(
            maximum_size=900,
            tightening_threshold=700
        )
        clamp.set_child(content)

        view = Adw.ToolbarView()
        view.add_top_bar(header)
        view.set_content(clamp)

        self.set_content(view)

    def _section_label(self, text):
        lbl = Gtk.Label(label=text)
        lbl.set_halign(Gtk.Align.START)
        lbl.add_css_class("section-title")
        return lbl

    # -------------------------------------------------
    # Config
    # -------------------------------------------------
    def _load_config(self):
        try:
            api_key, model = load_config()
            self.client = OpenAIClient(api_key, model)
        except ConfigError as e:
            self._show_error("Configuration required", str(e))

    # -------------------------------------------------
    # Actions
    # -------------------------------------------------
    def on_clear(self, _):
        self.input_view.get_buffer().set_text("")
        self.output_view.get_buffer().set_text("")
        self.custom_prompt_entry.set_text("")
        self.custom_prompt_entry.set_visible(False)
        self.prompt_dropdown.set_selected(0)

    def on_send(self, _):
        if not self.client or self.sending:
            return

        prompt = self._validate()
        if not prompt:
            return

        self._set_sending(True)
        self.output_view.get_buffer().set_text("")

        threading.Thread(
            target=self._send_async,
            args=(prompt,),
            daemon=True
        ).start()

    def _send_async(self, prompt):
        try:
            for chunk in self.client.stream(prompt):
                if self.cancel_stream:
                    break
                GLib.idle_add(self._append_response, chunk)
        except Exception as e:
            GLib.idle_add(
                self._show_error,
                "Request failed",
                str(e)
            )
        finally:
            GLib.idle_add(self._set_sending, False)

    def _append_response(self, text):
        buffer = self.output_view.get_buffer()
        buffer.insert(buffer.get_end_iter(), text)

        if self.auto_scroll:
            mark = buffer.create_mark(None, buffer.get_end_iter(), False)
            self.output_view.scroll_to_mark(mark, 0, True, 0, 1)

    def on_stop(self, _):
        if self.sending:
            self.cancel_stream = True

    def _set_sending(self, sending):
        self.sending = sending
        self.cancel_stream = False

        self.send_btn.set_sensitive(not sending)
        self.clear_btn.set_sensitive(not sending)
        self.input_view.set_sensitive(not sending)
        self.stop_btn.set_sensitive(sending)

        if sending:
            self.spinner.start()
        else:
            self.spinner.stop()

    # -------------------------------------------------
    # Prompt handling
    # -------------------------------------------------
    def on_prompt_changed(self, dropdown, _):
        selected = dropdown.get_selected()
        is_custom = self.prompt_options[selected] == "Write your own prompt"
        self.custom_prompt_entry.set_visible(is_custom)

    def _get_instruction(self):
        option = self.prompt_options[self.prompt_dropdown.get_selected()]
        if option == "Write your own prompt":
            return self.custom_prompt_entry.get_text().strip()
        return option

    def _validate(self):
        requires_text = False # init a flag
        buffer = self.input_view.get_buffer()
        text = buffer.get_text(
            buffer.get_start_iter(),
            buffer.get_end_iter(),
            True
        ).strip()

        instruction = self._get_instruction()
        prompt = ""

        if instruction in self.prompt_options or not instruction:
            requires_text = True
        
        if requires_text and not text:
            # raise error
            self._show_error(
                "Nothing to send",
                "Please enter a prompt or some text before sending."
            )
        elif not requires_text:
            prompt = instruction
        else:
            prompt = f"{instruction} the following text:\n\n {text}".strip()

        print(prompt)
        return prompt

    # -------------------------------------------------
    # Clipboard & keyboard
    # -------------------------------------------------
    def on_paste_clipboard(self, _):
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.read_text_async(None, self._on_clipboard_text)

    def _on_clipboard_text(self, clipboard, result):
        try:
            text = clipboard.read_text_finish(result)
            if text:
                self.input_view.get_buffer().set_text(text)
        except Exception:
            self._show_error(
                "Clipboard error",
                "Unable to read text from clipboard."
            )

    def on_key_pressed(self, controller, keyval, keycode, state):
        if state & Gdk.ModifierType.CONTROL_MASK:
            if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
                self.on_send(None)
                return Gdk.EVENT_STOP
        return Gdk.EVENT_PROPAGATE

    # -------------------------------------------------
    # Errors
    # -------------------------------------------------
    def _show_error(self, title, message):
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=title,
            body=message,
        )
        dialog.add_response("ok", "OK")
        dialog.present()
