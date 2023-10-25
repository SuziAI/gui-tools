import dataclasses
import tkinter as tk

import PIL
from PIL import ImageTk

from src.auxiliary import BoxProperty, open_file_as_tk_image, _create_suzipu_images
from src.config import CHINESE_FONT_FILE
from src.suzipu import SuzipuMelodySymbol, suzipu_to_info, SuzipuAdditionalSymbol, Symbol


def exec_quick_fill_window_text(annotation_type_var, max_length_var):
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
        if len(text_variable.get()) > 0:
            text_variable.set(text_variable.get()[0:max_length])

        left_character_string.set(f"{len(text_variable.get())}/{max_length} characters")

        if len(text_variable.get()) == max_length:
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


class TextAnnotationFrame:
    def __init__(self, window_handle, current_text_annotation_variable, quick_fill_vars, on_fill_all_boxes_of_type):
        self.window_handle = window_handle
        self.current_text_annotation_variable = current_text_annotation_variable
        self.quick_fill_vars = quick_fill_vars
        self.on_fill_all_boxes_of_type = on_fill_all_boxes_of_type

        self.frame = tk.LabelFrame(self.window_handle, text="Text Annotation")
        self._widgets = []

        self._create_frame()

    def _create_frame(self):
        def on_quick_fill():
            exit_save_var, text_variable = exec_quick_fill_window_text(*self.quick_fill_vars)
            if exit_save_var:
                self.on_fill_all_boxes_of_type(text_variable)

        self._widgets.append(tk.Entry(self.frame, width=2, font="Arial 25",
                                      textvariable=self.current_text_annotation_variable,
                                      state="disabled"))
        self._widgets.append(tk.Button(self.frame, text="Quick Fill...", command=on_quick_fill, state="disabled"))

        for widget in self._widgets:
            widget.pack(padx=10, pady=5)

    def get_frame(self):
        return self.frame

    def set_state(self, boolean):
        state = "disabled"
        if boolean:
            state = "normal"
        for widget in self._widgets:
            widget.config(state=state)


class SuzipuAnnotationFrame:
    def __init__(self, window_handle, first_musical_var, second_musical_var, on_change_annotation=lambda: None, quick_fill_vars=[], on_fill_all_boxes_of_type=lambda: None):
        self.window_handle = window_handle
        self.frame = tk.LabelFrame(self.window_handle, text="Suzipu Annotation")
        self.first_musical_var = first_musical_var
        self.second_musical_var = second_musical_var
        self.on_change_annotation = on_change_annotation
        self.quick_fill_vars = quick_fill_vars
        self.on_fill_all_boxes_of_type = on_fill_all_boxes_of_type

        self.display_first_symbol = None
        self.display_second_symbol = None

        self._widgets = []
        self._button_images = _create_suzipu_images()

        self._create_frame()

    def update_musical_display_image(self):
        self.display_first_symbol.config(image=self._button_images[str(self.first_musical_var.get())])
        self.display_second_symbol.config(image=self._button_images[str(self.second_musical_var.get())])

    def _create_frame(self):
        current_suzipu_choice_frame = tk.Frame(self.frame)
        self.display_first_symbol = tk.Label(current_suzipu_choice_frame,
                                        image=self._button_images[Symbol.NONE],
                                        relief="sunken", state="disabled")
        self.display_second_symbol = tk.Label(current_suzipu_choice_frame,
                                         image=self._button_images[Symbol.NONE],
                                         relief="sunken", state="disabled")

        def construct_suzipu_frame(frame, musical_var, prefix):
            second_symbol_frame = tk.LabelFrame(frame, text=f"{prefix} Symbol")

            none_button = tk.Radiobutton(second_symbol_frame, image=self._button_images[Symbol.NONE],
                                         variable=musical_var,
                                         value="None", indicator=0, state="disabled",
                                         command=lambda: [self.on_change_annotation(), self.update_musical_display_image()])
            none_button.grid(row=0, column=0)
            self._widgets.append(none_button)

            for idx, melody_var in enumerate(dataclasses.astuple(SuzipuMelodySymbol())):
                current_button = tk.Radiobutton(second_symbol_frame, image=self._button_images[melody_var],
                                                variable=musical_var,
                                                value=melody_var, indicator=0, state="disabled",
                                                command=lambda: [self.on_change_annotation(), self.update_musical_display_image()])
                self._widgets.append(current_button)
                current_button.grid(row=1, column=idx)
            for idx, additional_var in enumerate(dataclasses.astuple(SuzipuAdditionalSymbol())):
                current_button = tk.Radiobutton(second_symbol_frame, image=self._button_images[additional_var],
                                                variable=musical_var,
                                                value=additional_var, indicator=0, state="disabled",
                                                command=lambda: [self.on_change_annotation(), self.update_musical_display_image()])
                self._widgets.append(current_button)
                current_button.grid(row=2, column=idx)
            return second_symbol_frame

        def on_quick_fill():
            exit_save_var, text_variable = exec_quick_fill_window_suzipu(*self.quick_fill_vars)
            if exit_save_var:
                self.on_fill_all_boxes_of_type(text_variable)

        quick_fill_button = tk.Button(self.frame, text="Quick Fill...", command=on_quick_fill, state="disabled")

        self.display_first_symbol.grid(row=0, column=0, padx=10)
        self.display_second_symbol.grid(row=1, column=0, padx=10)
        self._widgets += [self.display_first_symbol, self.display_second_symbol, quick_fill_button]

        symbol_frames = tk.Frame(self.frame)
        construct_suzipu_frame(symbol_frames, self.first_musical_var, "First").grid(row=0, column=0, padx=10, pady=5)  # upper frame
        construct_suzipu_frame(symbol_frames, self.second_musical_var, "Second").grid(row=1, column=0, padx=10, pady=5)  # lower frame
        quick_fill_button.grid(row=2, column=0, padx=10, pady=10)

        current_suzipu_choice_frame.grid(row=0, column=0)
        symbol_frames.grid(row=0, column=1)

    def get_frame(self):
        return self.frame

    def set_state(self, boolean):
        state = "disabled"
        if boolean:
            state = "normal"
        for widget in self._widgets:
            widget.config(state=state)


class BoxSelectionFrame:
    def __init__(self, window_handle, display_variable, on_previous=lambda: None, on_next=lambda: None):
        self.window_handle = window_handle
        self.frame = tk.Frame(self.window_handle)
        self.display_variable = display_variable
        self.on_previous = on_previous
        self.on_next = on_next

        self._widgets = []

        self._create_frame()

    def _create_frame(self):
        previous_button = tk.Button(self.frame, text="<< Previous", command=self.on_previous, state="disabled", width=10)
        previous_button.grid(row=0, column=0)
        current_box_index_display = tk.Label(self.frame, height=1, width=10, textvariable=self.display_variable,
                                             relief="sunken", state="disabled")
        current_box_index_display.grid(row=0, column=1)
        next_button = tk.Button(self.frame, text="Next >>", command=self.on_next, state="disabled", width=10)
        next_button.grid(row=0, column=2)

        self._widgets = [previous_button, current_box_index_display, next_button]

    def get_frame(self):
        return self.frame

    def set_state(self, boolean):
        state = "disabled"
        if boolean:
            state = "normal"
        for widget in self._widgets:
            widget.config(state=state)


class AnnotationFrame:
    def __init__(self, window_handle, boxtype_variable,
                 display_variable, type_length_variable,
                 current_annotation_text_variable,
                 musical_vars,
                 current_box_is_excluded,
                 current_box_is_line_break,
                 on_previous=lambda: None, on_next=lambda: None,
                 on_change_annotation=lambda: None, on_fill_all_boxes_of_type=lambda: None):
        self.window_handle = window_handle
        self.boxtype_variable = boxtype_variable
        self.display_variable = display_variable
        self.type_length_variable = type_length_variable
        self.current_annotation_text_variable = current_annotation_text_variable
        self.musical_vars = musical_vars
        self.current_box_is_excluded = current_box_is_excluded
        self.current_box_is_line_break = current_box_is_line_break
        self.on_previous = lambda: [on_previous(), self.update_musical_image_display()]
        self.on_next = lambda: [on_next(), self.update_musical_image_display()]
        self.on_change_annotation = lambda: [on_change_annotation(), self.update_musical_image_display()]
        self.on_fill_all_boxes_of_type = on_fill_all_boxes_of_type

        self.frame = tk.LabelFrame(self.window_handle, text="Annotation")
        self.image = None

        self.current_box_image_display = tk.Label(self.frame, image=None, relief="sunken", state="disabled")
        self.selection_frame = BoxSelectionFrame(self.frame, self.display_variable,
                                                 self.on_previous,
                                                 self.on_next)

        self.text_annotation = None
        self.suzipu_annotation = None
        self.box_excluded_checkbox = None

        self._create_frame()

    def set_state(self, boolean):
        self.current_box_image_display.configure(state="normal" if boolean else "disabled")
        self.box_excluded_checkbox.configure(state="normal" if boolean else "disabled")
        self.box_line_break_checkbox.configure(state="normal" if boolean else "disabled")

        self.selection_frame.set_state(boolean)
        if boolean:
            if self.boxtype_variable.get() == BoxProperty.MUSIC:
                self.suzipu_annotation.set_state(True)
                self.text_annotation.set_state(False)
            else:
                self.suzipu_annotation.set_state(False)
                self.text_annotation.set_state(True)
        else:
            self.suzipu_annotation.set_state(False)
            self.text_annotation.set_state(False)

    def set_image(self, image):
        self.current_box_image_display.configure(image=image)

    def update_musical_image_display(self):
        self.suzipu_annotation.update_musical_display_image()

    def _create_frame(self):
        annotations_frame = tk.Frame(self.frame)
        self.text_annotation = TextAnnotationFrame(annotations_frame, self.current_annotation_text_variable,
                                                   [self.boxtype_variable, self.type_length_variable],
                                                   self.on_fill_all_boxes_of_type)
        self.text_annotation.get_frame().grid(row=0, column=0, padx=10, pady=20)
        self.suzipu_annotation = SuzipuAnnotationFrame(annotations_frame, *self.musical_vars, self.on_change_annotation, [self.boxtype_variable, self.type_length_variable],
                                                   self.on_fill_all_boxes_of_type)
        self.suzipu_annotation.get_frame().grid(row=0, column=1, padx=10, pady=20)
        self.box_excluded_checkbox = tk.Checkbutton(annotations_frame, text='Exclude this box from dataset',
                                                    variable=self.current_box_is_excluded, onvalue=True,
                                                    offvalue=False, command=self.on_change_annotation, state="disabled")
        self.box_line_break_checkbox = tk.Checkbutton(annotations_frame, text='Column break occurs after this box',
                                                    variable=self.current_box_is_line_break, onvalue=True,
                                                    offvalue=False, command=self.on_change_annotation, state="disabled")
        self.current_box_image_display.grid(row=0, column=1)
        self.selection_frame.get_frame().grid(row=1, column=1)
        annotations_frame.grid(row=2, column=1)

        self.box_excluded_checkbox.grid(row=3, column=0, sticky="W")
        self.box_line_break_checkbox.grid(row=4, column=0, sticky="W")

    def get_frame(self):
        return self.frame
