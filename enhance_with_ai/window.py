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

        self.cancel_stream = False
        self.auto_scroll = True

        self.prompt_options = [
            "Summarize",
            "Explain",
            "Enhance",
            "Proofread",
            "Write your own"
        ]


        self.set_title("Enhance With AI")
        self.set_default_size(800, 600)

        self.client = None
        self.sending = False

        # --- Toolbar / HeaderBar ---
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Enhance With AI"))

        # Paste from clipboard
        clipboard_btn = Gtk.Button(
            icon_name="edit-paste-symbolic",
            tooltip_text="Paste from clipboard"
        )
        clipboard_btn.connect("clicked", self.on_paste_clipboard)
        header.pack_start(clipboard_btn)

        # Auto-scroll toggle
        self.autoscroll_btn = Gtk.ToggleButton(
            icon_name="go-down-symbolic",
            tooltip_text="Auto-scroll output"
        )
        self.autoscroll_btn.set_active(True)
        self.autoscroll_btn.connect(
            "toggled",
            lambda b: setattr(self, "auto_scroll", b.get_active())
        )
        header.pack_start(self.autoscroll_btn)

        # Stop button
        self.stop_btn = Gtk.Button(
            icon_name="media-playback-stop-symbolic",
            tooltip_text="Stop response"
        )
        self.stop_btn.set_sensitive(False)
        self.stop_btn.connect("clicked", self.on_stop)
        header.pack_end(self.stop_btn)

        # Spinner
        self.spinner = Gtk.Spinner()
        header.pack_end(self.spinner)


        """     
        # Clipboard button
        clipboard_btn = Gtk.Button(
            icon_name="edit-paste-symbolic",
            tooltip_text="Paste from clipboard"
        )
        clipboard_btn.connect("clicked", self.on_paste_clipboard)
        header.pack_start(clipboard_btn)

        # Spinner (activity indicator)
        self.spinner = Gtk.Spinner()
        header.pack_end(self.spinner) """


        # --- Main content ---
        #self.prompt_entry = Gtk.Entry(
        #    placeholder_text="Quick prompt"
        #)

        # The new dropdown
        # Instruction selector
        self.prompt_dropdown = Gtk.DropDown.new_from_strings(self.prompt_options)
        self.prompt_dropdown.set_selected(0)
        self.prompt_dropdown.connect(
            "notify::selected",
            self.on_prompt_changed
        )

        # Custom instruction entry (hidden by default)
        self.custom_prompt_entry = Gtk.Entry()
        self.custom_prompt_entry.set_placeholder_text("Write your instruction…")
        self.custom_prompt_entry.set_visible(False)

        prompt_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=6
        )
        prompt_box.append(self.prompt_dropdown)
        prompt_box.append(self.custom_prompt_entry)
        # end dropdown menu

        self.input_view = Gtk.TextView(
            wrap_mode=Gtk.WrapMode.WORD_CHAR
        )

        input_scroll = Gtk.ScrolledWindow(vexpand=True)
        input_scroll.set_child(self.input_view)

        self.output_view = Gtk.TextView(
            editable=False,
            wrap_mode=Gtk.WrapMode.WORD_CHAR
        )

        output_scroll = Gtk.ScrolledWindow(vexpand=True)
        output_scroll.set_child(self.output_view)

        # Buttons
        self.clear_btn = Gtk.Button(label="Clear")
        self.clear_btn.connect("clicked", self.on_clear)

        self.send_btn = Gtk.Button(label="Send")
        self.send_btn.add_css_class("suggested-action")
        self.send_btn.connect("clicked", self.on_send)

        button_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=6,
            halign=Gtk.Align.END,
        )
        button_box.append(self.clear_btn)
        button_box.append(self.send_btn)

        # Layout box
        content = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
            margin_top=12,
            margin_bottom=12,
            margin_start=12,
            margin_end=12,
        )
        #content.append(self.prompt_entry)
        content.append(prompt_box) #  The new menu
        content.append(input_scroll)
        content.append(button_box)
        content.append(output_scroll)

        # ToolbarView (MANDATORY)
        view = Adw.ToolbarView()
        view.add_top_bar(header)
        view.set_content(content)
        

        self.set_content(view)

        self._load_config()

        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)

        self.add_controller(key_controller)

    # ----------------------------
    # Config
    # ----------------------------
    def _load_config(self):
        try:
            api_key, model = load_config()
            self.client = OpenAIClient(api_key, model)
        except ConfigError as e:
            self._show_error("Configuration required", str(e))

    # ----------------------------
    # UI State helpers
    # ----------------------------
    def _set_sending(self, sending: bool):
        self.sending = sending
        self.send_btn.set_sensitive(not sending)
        self.clear_btn.set_sensitive(not sending)
        #self.prompt_entry.set_sensitive(not sending)
        self.input_view.set_sensitive(not sending)

        if sending:
            self.spinner.start()
        else:
            self.spinner.stop()

    # ----------------------------
    # Validation
    # ----------------------------
    def _validate(self):
        buffer = self.input_view.get_buffer()
        text = buffer.get_text(
            buffer.get_start_iter(),
            buffer.get_end_iter(),
            True,
        ).strip()

        instruction = self._get_instruction()

        if instruction and text:
            instruction = f"{instruction} the following text:\n\n{text}"
        elif text and not instruction:
            instruction = text
        elif not text and not instruction:
            self._show_error(
                "Nothing to send",
                "Please enter a prompt or some text before sending."
            )
            return None

        return instruction

    # ----------------------------
    # Actions
    # ----------------------------
    def on_clear(self, _):
        self.input_view.get_buffer().set_text("")
        self.output_view.get_buffer().set_text("")
        #self.prompt_entry.set_text("")
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

        # Run API call in background thread (desktop requirement)
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
        end = buffer.get_end_iter()
        buffer.insert(end, text)

        if self.auto_scroll:
            mark = buffer.create_mark(None, buffer.get_end_iter(), False)
            self.output_view.scroll_to_mark(
                mark,
                0.0,
                True,
                0.0,
                1.0
            )



    # ----------------------------
    # UI feedback
    # ----------------------------
    def _show_response(self, text):
        self.output_view.get_buffer().set_text(text)

    def _show_error(self, title, message):
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=title,
            body=message,
        )
        dialog.add_response("ok", "OK")
        dialog.present()

    def on_paste_clipboard(self, _):
        display = Gdk.Display.get_default()
        clipboard = display.get_clipboard()

        clipboard.read_text_async(
            None,
            self._on_clipboard_text
        )

    def _on_clipboard_text(self, clipboard, result):
        try:
            text = clipboard.read_text_finish(result)
            if text:
                self.input_view.get_buffer().set_text(text)
        except Exception as e:
            self._show_error(
                "Clipboard error",
                "Unable to read text from clipboard."
            )

    def on_key_pressed(self, controller, keyval, keycode, state):
        if state & Gdk.ModifierType.CONTROL_MASK:
            if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
                self.on_send(None)
                return Gdk.EVENT_STOP  # Explicitly consume event
        return Gdk.EVENT_PROPAGATE

    def on_stop(self, _):
        if self.sending:
            self.cancel_stream = True
        
    def _set_sending(self, sending: bool):
        self.sending = sending
        self.cancel_stream = False

        self.send_btn.set_sensitive(not sending)
        self.clear_btn.set_sensitive(not sending)
        #self.prompt_entry.set_sensitive(not sending)
        self.input_view.set_sensitive(not sending)
        self.stop_btn.set_sensitive(sending)

        if sending:
            self.spinner.start()
        else:
            self.spinner.stop()

    def on_prompt_changed(self, dropdown, _):
        selected = dropdown.get_selected()
        is_custom = self.prompt_options[selected] == "Write your own"
        self.custom_prompt_entry.set_visible(is_custom)

    def _get_instruction(self):
        option = self.prompt_options[self.prompt_dropdown.get_selected()]

        if option == "Write your own":
            return self.custom_prompt_entry.get_text().strip()

        return option.lower()
