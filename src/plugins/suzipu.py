import dataclasses
import tkinter as tk

from src.config import CHINESE_FONT_FILE
from src.plugins.suzipu_lvlvpu_gongchepu.common import Symbol, SuzipuMelodySymbol, SuzipuAdditionalSymbol, \
    _create_suzipu_images, ModeSelectorFrame


class NotationAnnotationFrame:
    def __init__(self, window_handle, first_musical_var, second_musical_var,
                 on_change_annotation=lambda: None, quick_fill_vars=[], on_fill_all_boxes_of_type=lambda: None,
                 mode_variable=None, get_mode_string=lambda: None):
        self.window_handle = window_handle
        self.frame = tk.Frame(self.window_handle)
        self.first_musical_var = first_musical_var
        self.second_musical_var = second_musical_var
        self.on_change_annotation = on_change_annotation
        self.quick_fill_vars = quick_fill_vars
        self.on_fill_all_boxes_of_type = on_fill_all_boxes_of_type
        self.mode_variable = mode_variable
        self.get_mode_string = get_mode_string

        self.mode_selector = None

        self.display_first_symbol = None
        self.display_second_symbol = None

        self._widgets = []
        self._button_images = _create_suzipu_images()

        self._create_frame()

    def update_musical_display_image(self):
        self.display_first_symbol.config(image=self._button_images[str(self.first_musical_var.get())])
        self.display_second_symbol.config(image=self._button_images[str(self.second_musical_var.get())])

    def _create_frame(self):
        self.mode_selector = ModeSelectorFrame(self.frame, mode_variable=self.mode_variable, on_get_mode_string=self.get_mode_string)

        mode_selector_frame = self.mode_selector.get_frame()
        annotator_frame = tk.Frame(self.frame)

        current_suzipu_choice_frame = tk.Frame(annotator_frame)
        self.display_first_symbol = tk.Label(current_suzipu_choice_frame,
                                             image=self._button_images[Symbol.NONE],
                                             relief="sunken", state="disabled")
        self.display_second_symbol = tk.Label(current_suzipu_choice_frame,
                                              image=self._button_images[Symbol.NONE],
                                              relief="sunken", state="disabled")

        def construct_suzipu_frame(frame, musical_var, primary=True):
            prefix = "Pitch" if primary else "Secondary"
            symbol_frame = tk.LabelFrame(frame, text=f"{prefix} Symbol")

            none_button = tk.Radiobutton(symbol_frame, image=self._button_images[Symbol.NONE],
                                         variable=musical_var,
                                         value="None", indicator=0, state="disabled",
                                         command=lambda: [self.on_change_annotation(), self.update_musical_display_image()])
            none_button.grid(row=0, column=0)
            self._widgets.append(none_button)

            if primary:
                for idx, melody_var in enumerate(dataclasses.astuple(SuzipuMelodySymbol())):
                    current_button = tk.Radiobutton(symbol_frame, image=self._button_images[melody_var],
                                                    variable=musical_var,
                                                    value=melody_var, indicator=0, state="disabled",
                                                    command=lambda: [self.on_change_annotation(), self.update_musical_display_image()])
                    self._widgets.append(current_button)
                    current_button.grid(row=0, column=idx+1)
            else:
                for idx, additional_var in enumerate(dataclasses.astuple(SuzipuAdditionalSymbol())):
                    current_button = tk.Radiobutton(symbol_frame, image=self._button_images[additional_var],
                                                    variable=musical_var,
                                                    value=additional_var, indicator=0, state="disabled",
                                                    command=lambda: [self.on_change_annotation(), self.update_musical_display_image()])
                    self._widgets.append(current_button)
                    current_button.grid(row=0, column=idx+1)
            return symbol_frame

        def on_quick_fill():
            exit_save_var, text_variable = exec_quick_fill_window_suzipu(*self.quick_fill_vars)
            if exit_save_var:
                self.on_fill_all_boxes_of_type(text_variable)

        quick_fill_button = tk.Button(annotator_frame, text="Quick Fill...", command=on_quick_fill, state="disabled")

        self.display_first_symbol.grid(row=0, column=0, padx=10)
        self.display_second_symbol.grid(row=1, column=0, padx=10)
        self._widgets += [self.display_first_symbol, self.display_second_symbol, quick_fill_button]

        symbol_frames = tk.Frame(annotator_frame)
        construct_suzipu_frame(symbol_frames, self.first_musical_var, True).grid(sticky="W", row=0, column=0, padx=10, pady=5)  # upper frame
        construct_suzipu_frame(symbol_frames, self.second_musical_var, False).grid(sticky="W", row=1, column=0, padx=10, pady=5, columnspan=2)  # lower frame

        symbol_frames.grid(row=0, column=1)
        current_suzipu_choice_frame.grid(row=0, column=0)
        quick_fill_button.grid(row=1, column=0, padx=10, pady=10)

        mode_selector_frame.grid(row=0, column=0)
        annotator_frame.grid(row=1, column=0)

    def get_frame(self):
        return self.frame

    def set_state(self, boolean):
        state = "disabled"
        if boolean:
            state = "normal"
        for widget in self._widgets:
            widget.config(state=state)

    def set_mode_properties(self, props: dict):
        self.mode_selector.set_properties(props)

    def get_mode_properties(self):
        return self.mode_selector.get_properties()


def exec_quick_fill_window_suzipu(annotation_type_var, max_length_var):
    quick_fill_window = tk.Toplevel()

    exit_save_var = tk.BooleanVar()
    exit_save_var.set(False)
    def on_destroy_save_changes():
        exit_save_var.set(True)
        quick_fill_window.destroy()

    annotation_type = annotation_type_var.get()
    max_length = int(max_length_var.get())

    quick_fill_window.title(f"Quick Fill {annotation_type}")

    text_variable = tk.StringVar(quick_fill_window)
    text_variable.set("")

    left_character_string = tk.StringVar(quick_fill_window)
    left_character_string.set("")
    ok_button = tk.Button(quick_fill_window, text="OK", command=on_destroy_save_changes, state="disabled")

    def on_change_text(*args):
        #if len(text_variable.get()) > 0:
        #    text_variable.set(text_variable.get()[0:max_length])
        cell_number = len(text_variable.get().split("|"))
        left_character_string.set(f"{cell_number}/{max_length} cells (separator: '|')")

        if cell_number == max_length:
            ok_button.configure(state="normal")
        else:
            ok_button.configure(state="disabled")

    text_variable.trace("w", on_change_text)

    tk.Entry(quick_fill_window, width=min(max_length * 2, 20), font=CHINESE_FONT_FILE,
             # use *2, because Chinese characters have double width
             textvariable=text_variable).pack()
    tk.Label(quick_fill_window, textvariable=left_character_string).pack()
    ok_button.pack()
    on_change_text()

    quick_fill_window.wait_window()

    return exit_save_var.get(), text_variable.get()