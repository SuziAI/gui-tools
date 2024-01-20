import tkinter as tk
import tkinter.ttk

from src.auxiliary import BoxProperty
from src.config import CHINESE_FONT_FILE
from src.intelligent_assistant import predict_from_images
import importlib


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


def exec_intelligent_fill_window_text(annotation_type_var, max_length_var, get_box_images):
    quick_fill_window = tk.Toplevel()

    exit_save_var = tk.BooleanVar()
    exit_save_var.set(False)

    prediction = tk.StringVar()

    def on_predict():
        exit_save_var.set(True)
        image_list = get_box_images(annotation_type)
        progress = tk.IntVar(value=0)

        def predict(update):
            local_prediction = predict_from_images(image_list, progress, update)
            if not local_prediction:
                exit_save_var.set(False)

            prediction.set(local_prediction)

        def wait(message):
            win = tk.Toplevel()
            win.title('Wait')
            tk.Label(win, text=message, padx=10, pady=10).pack()
            tkinter.ttk.Progressbar(win, length=100, orient=tk.HORIZONTAL, variable=progress).pack(pady=10)
            return win

        win = wait("Intelligent text prediction in progress.")
        quick_fill_window.wait_visibility(win)
        win.update()

        predict(update=win.update)
        win.destroy()

        quick_fill_window.destroy()

    annotation_type = annotation_type_var.get()
    quick_fill_window.title(f"Intelligent Fill {annotation_type}")

    tk.Label(quick_fill_window, padx=10, pady=10, text=f"Intelligent Fill tries to recognize the characters from the\nsegmentation boxes of type {annotation_type}.\nIt might take a while, and all textual content is overwritten.\nProceed?").pack()

    button_frame = tk.Frame(quick_fill_window)
    tk.Button(button_frame, text="OK", command=on_predict).grid(column=0, row=0)
    tk.Button(button_frame, text="Cancel", command=quick_fill_window.destroy).grid(column=1, row=0)
    button_frame.pack()

    quick_fill_window.wait_window()

    return exit_save_var.get(), prediction.get()


class TextAnnotationFrame:
    def __init__(self, window_handle, current_text_annotation_variable, quick_fill_vars, on_fill_all_boxes_of_type, get_box_images):
        self.window_handle = window_handle
        self.current_text_annotation_variable = current_text_annotation_variable
        self.quick_fill_vars = quick_fill_vars
        self.on_fill_all_boxes_of_type = on_fill_all_boxes_of_type
        self.get_box_images = get_box_images

        self.frame = tk.LabelFrame(self.window_handle, text="Text Annotation")
        self._widgets = []

        self._create_frame()

    def _create_frame(self):
        def on_quick_fill():
            exit_save_var, text_variable = exec_quick_fill_window_text(*self.quick_fill_vars)
            if exit_save_var:
                self.on_fill_all_boxes_of_type(text_variable)

        def on_intelligent_fill():
            exit_save_var, prediction = exec_intelligent_fill_window_text(*self.quick_fill_vars, self.get_box_images)
            if exit_save_var:
                self.on_fill_all_boxes_of_type(prediction)

        self._widgets.append(tk.Entry(self.frame, width=2, font="Arial 25",
                                      textvariable=self.current_text_annotation_variable,
                                      state="disabled"))
        self._widgets.append(tk.Button(self.frame, text="Quick Fill...", command=on_quick_fill, state="disabled"))
        self._widgets.append(tk.Button(self.frame, text="Intelligent Fill...", command=on_intelligent_fill, state="disabled"))

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
                 on_change_annotation=lambda: None,
                 on_fill_all_boxes_of_type=lambda: None,
                 get_box_images=lambda: None,
                 mode_variable=None,
                 get_mode_string=lambda: None):
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
        self.get_box_images = get_box_images
        self.mode_variable = mode_variable
        self.get_mode_string = get_mode_string

        self.frame = tk.LabelFrame(self.window_handle, text="Annotation")
        self.image = None

        self.current_box_image_display = tk.Label(self.frame, image=None, relief="sunken", state="disabled")
        self.selection_frame = BoxSelectionFrame(self.frame, self.display_variable,
                                                 self.on_previous,
                                                 self.on_next)

        self.text_annotation = None
        self.musical_annotation_frame = None
        self.box_excluded_checkbox = None

        self._create_frame()

    def set_state(self, boolean):
        self.current_box_image_display.configure(state="normal" if boolean else "disabled")
        self.box_excluded_checkbox.configure(state="normal" if boolean else "disabled")
        self.box_line_break_checkbox.configure(state="normal" if boolean else "disabled")

        self.selection_frame.set_state(boolean)
        if boolean:
            if self.boxtype_variable.get() == BoxProperty.MUSIC:
                self.musical_annotation_frame.set_state(True)
                self.text_annotation.set_state(False)
            else:
                self.musical_annotation_frame.set_state(False)
                self.text_annotation.set_state(True)
        else:
            self.musical_annotation_frame.set_state(False)
            self.text_annotation.set_state(False)

    def set_image(self, image):
        self.current_box_image_display.configure(image=image)

    def update_musical_image_display(self):
        self.musical_annotation_frame.update_musical_display_image()

    def _create_frame(self):

        module = importlib.import_module("src.plugins.suzipu")

        annotations_frame = tk.Frame(self.frame)
        self.text_annotation = TextAnnotationFrame(annotations_frame, self.current_annotation_text_variable,
                                                   [self.boxtype_variable, self.type_length_variable],
                                                   self.on_fill_all_boxes_of_type, self.get_box_images)
        self.text_annotation.get_frame().grid(row=0, column=0, padx=10, pady=20)
        music_frame = tk.LabelFrame(annotations_frame, text="Musical Annotation");
        self.musical_annotation_frame = module.NotationAnnotationFrame(music_frame, *self.musical_vars,
                                           self.on_change_annotation,
                                           [self.boxtype_variable, self.type_length_variable],
                                           self.on_fill_all_boxes_of_type, self.mode_variable, self.get_mode_string)
        self.musical_annotation_frame.get_frame().pack()
        music_frame.grid(row=0, column=1, padx=10, pady=20)
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

    def set_mode_properties(self, props: dict):
        self.musical_annotation_frame.set_mode_properties(props)

    def get_mode_properties(self):
        return self.musical_annotation_frame.get_mode_properties()

    def get_frame(self):
        return self.frame
