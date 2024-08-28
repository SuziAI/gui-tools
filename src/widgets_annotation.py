import tkinter as tk
import tkinter.ttk

from src.auxiliary import BoxType
from src.config import CHINESE_FONT_FILE
from src.intelligent_assistant import predict_text_from_images
import importlib

from src.programstate import ProgramState


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

    text_variable.trace_add("write", on_change_text)

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

    prediction_title = tk.StringVar()
    prediction_mode = tk.StringVar()
    prediction_preface = tk.StringVar()
    prediction_lyrics = tk.StringVar()
    prediction_lyrics_ind = tk.StringVar()
    prediction_unmarked = tk.StringVar()

    def on_predict():
        exit_save_var.set(True)
        image_list_title = get_box_images(BoxType.TITLE)
        image_list_mode = get_box_images(BoxType.MODE)
        image_list_preface = get_box_images(BoxType.PREFACE)
        image_list_lyrics = get_box_images(BoxType.LYRICS)
        image_list_lyrics_ind = get_box_images(BoxType.LYRICS_IND)
        image_list_unmarked = get_box_images(BoxType.UNMARKED)

        total_progress = len(image_list_title) + len(image_list_mode) + len(image_list_preface) + len(image_list_lyrics) + len(image_list_unmarked) + len(image_list_lyrics_ind)

        progress = tk.DoubleVar(value=0)

        def predict(update):
            prediction_title.set(predict_text_from_images(image_list_title, progress, total_progress, update))
            prediction_mode.set(predict_text_from_images(image_list_mode, progress, total_progress, update))
            prediction_preface.set(predict_text_from_images(image_list_preface, progress, total_progress, update))
            prediction_lyrics.set(predict_text_from_images(image_list_lyrics, progress, total_progress, update))
            prediction_lyrics_ind.set(predict_text_from_images(image_list_lyrics_ind, progress, total_progress, update))
            prediction_unmarked.set(predict_text_from_images(image_list_unmarked, progress, total_progress, update))

            if not prediction_title and not prediction_mode and not prediction_preface and not prediction_lyrics and not prediction_lyrics_ind and not prediction_unmarked:
                exit_save_var.set(False)

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

    quick_fill_window.title(f"Intelligent Fill")

    tk.Label(quick_fill_window, padx=10, pady=10, text=f"Intelligent Fill tries to recognize the characters from all boxes containing textual data.\nIt might take a while, and all textual content is overwritten.\nProceed?").pack()

    button_frame = tk.Frame(quick_fill_window)
    tk.Button(button_frame, text="OK", command=on_predict).grid(column=0, row=0)
    tk.Button(button_frame, text="Cancel", command=quick_fill_window.destroy).grid(column=1, row=0)
    button_frame.pack()

    quick_fill_window.wait_window()

    return exit_save_var.get(), prediction_title.get(), prediction_mode.get(), prediction_preface.get(), prediction_lyrics.get(), prediction_lyrics_ind.get(), prediction_unmarked.get()


class TextAnnotationFrame:
    def __init__(self, window_handle, program_state: ProgramState):
        self.window_handle = window_handle
        self.program_state = program_state
        self.quick_fill_vars = [self.program_state.gui_state.tk_current_boxtype, self.program_state.gui_state.tk_num_all_boxes_of_current_type]

        self.frame = tk.LabelFrame(self.window_handle, text="Text Annotation")

        def update_variable(*args):
            max_limit = 2
            # text-based characters can only be annotated with up to two characters
            if len(self.box_annotation_string.get()) >= max_limit:
                self.box_annotation_string.set(self.box_annotation_string.get()[0:max_limit])
            self.program_state.set_current_annotation(self.box_annotation_string.get())

        self.box_annotation_string = tk.StringVar(self.frame, "")
        self.box_annotation_string.trace_add("write", update_variable)

        self._widgets = []
        self.state = False

        self._create_frame()

    def _create_frame(self):
        def on_quick_fill():
            exit_save_var, text_variable = exec_quick_fill_window_text(*self.quick_fill_vars)
            if exit_save_var:
                self.program_state.fill_all_boxes_of_current_type(text_variable)

        def on_intelligent_fill():
            exit_save_var, prediction_title, prediction_mode, prediction_preface, prediction_lyrics, prediction_lyrics_ind, prediction_unmarked = exec_intelligent_fill_window_text(*self.quick_fill_vars, self.program_state.get_box_images_from_type)
            if exit_save_var:
                if prediction_title:
                    self.program_state.fill_all_boxes_of_type(BoxType.TITLE, prediction_title)
                if prediction_mode:
                    self.program_state.fill_all_boxes_of_type(BoxType.MODE, prediction_mode)
                if prediction_preface:
                    self.program_state.fill_all_boxes_of_type(BoxType.PREFACE, prediction_preface)
                if prediction_lyrics:
                    self.program_state.fill_all_boxes_of_type(BoxType.LYRICS, prediction_lyrics)
                if prediction_lyrics_ind:
                    self.program_state.fill_all_boxes_of_type(BoxType.LYRICS_IND, prediction_lyrics_ind)
                if prediction_unmarked:
                    self.program_state.fill_all_boxes_of_type(BoxType.UNMARKED, prediction_unmarked)

        self._widgets.append(tk.Entry(self.frame, width=2, font="Arial 25",
                                      textvariable=self.box_annotation_string,
                                      state="disabled"))
        self._widgets.append(tk.Button(self.frame, text="Quick Fill...", command=on_quick_fill, state="disabled"))
        self._widgets.append(tk.Button(self.frame, text="Intelligent Fill...", command=on_intelligent_fill, state="disabled"))

        for widget in self._widgets:
            widget.pack(padx=10, pady=4)

    def get_frame(self):
        return self.frame

    def update_display(self):
        if self.state:
            set_str = self.program_state.get_current_annotation()
        else:
            set_str = ""
        self.box_annotation_string.set(set_str)

    def set_state(self, boolean):
        self.state = boolean
        state = "disabled"
        if boolean:
            state = "normal"
        for widget in self._widgets:
            widget.config(state=state)


class AnnotationFrame:
    def __init__(self, window_handle,
                 program_state: ProgramState,
                 get_mode_string=lambda: None):
        self.window_handle = window_handle
        self.program_state = program_state

        self.frame = tk.LabelFrame(self.window_handle, text="Annotation")
        self.image = None

        self.current_box_image_display = tk.Label(self.frame, image=None, relief="sunken", state="disabled")

        self.on_previous = lambda: [self.program_state.get_current_type_cycle().previous(), self.program_state.update_annotation_image_and_variables(), self.update_annotation()]
        self.on_next = lambda: [self.program_state.get_current_type_cycle().next(), self.program_state.update_annotation_image_and_variables(), self.update_annotation()]
        self.on_change_annotation = lambda: [self.program_state.save_annotation_to_box(), self.update_annotation()]

        self.widgets = []
        self.state = False

        self.text_annotation = None
        self.musical_annotation_frame = None
        self.box_excluded_checkbox = None

        self._create_frame()

    def set_state(self, boolean):
        self.box_excluded_checkbox.configure(state="normal" if boolean else "disabled")
        self.box_line_break_checkbox.configure(state="normal" if boolean else "disabled")

        self.state = boolean

        for widget in self.widgets:
            widget.config(state="normal" if boolean else "disabled")

        if boolean:
            self.current_box_image_display.configure(state="normal")
            if self.program_state.gui_state.tk_current_boxtype.get() in (BoxType.MUSIC, BoxType.MUSIC_IND):
                if self.musical_annotation_frame is not None:
                    self.musical_annotation_frame.set_state(True)
                self.text_annotation.set_state(False)
            else:
                if self.musical_annotation_frame is not None:
                    self.musical_annotation_frame.set_state(False)
                self.text_annotation.set_state(True)
        else:
            if self.musical_annotation_frame is not None:
                self.musical_annotation_frame.set_state(False)
            self.text_annotation.set_state(False)
            self.program_state.gui_state.tk_current_box_out_of_current_type.set("")
            self.current_box_image_display.configure(image=self.program_state.gui_state.empty_image)
            self.current_box_image_display.configure("disabled")

    def set_image(self, image):
        if self.state:
            set_img = image
        else:
            set_img = self.program_state.gui_state.empty_image
        self.current_box_image_display.configure(image=set_img)

    def update_annotation(self):
        self.set_image(self.program_state.gui_state.current_annotation_image)
        if self.program_state.get_current_type() in (BoxType.MUSIC, BoxType.MUSIC_IND):
            if self.musical_annotation_frame is not None:
                self.musical_annotation_frame.update_display()
        else:
            self.text_annotation.update_display()

    def _create_frame(self):
        annotations_frame = tk.Frame(self.frame)
        text_annotations_frame = tk.Frame(annotations_frame)
        self.text_annotation = TextAnnotationFrame(text_annotations_frame, program_state=self.program_state)
        self.text_annotation.get_frame().grid(row=0, column=0, padx=10, pady=10)
        music_frame = tk.LabelFrame(annotations_frame, text="Musical Annotation")

        def update_module(*args):
            if self.musical_annotation_frame is not None:
                self.musical_annotation_frame.get_frame().destroy()
            plugin_name = self.program_state.gui_state.tk_notation_plugin_selection.get().lower()
            module = importlib.import_module(f"src.plugins.{plugin_name}")
            self.musical_annotation_frame = module.NotationAnnotationFrame(music_frame, self.program_state)
            self.musical_annotation_frame.get_frame().pack()

        self.program_state.gui_state.tk_notation_plugin_selection.trace_add("write", update_module)

        music_frame.grid(row=0, column=1, padx=10, pady=10)

        def update_excluded(*args):
            self.program_state.piece_properties.content.set_index_excluded(
                self.program_state.get_current_annotation_index(),
                self.program_state.gui_state.tk_current_box_is_excluded.get())

        def update_line_break(*args):
            self.program_state.piece_properties.content.set_index_line_break(
                self.program_state.get_current_annotation_index(),
                self.program_state.gui_state.tk_current_box_is_line_break.get())

        box_frames = tk.Frame(text_annotations_frame)
        self.box_excluded_checkbox = tk.Checkbutton(box_frames, text='Exclude this box from dataset',
                                                    variable=self.program_state.gui_state.tk_current_box_is_excluded, onvalue=True,
                                                    offvalue=False, command=update_excluded, state="disabled")
        self.box_line_break_checkbox = tk.Checkbutton(box_frames, text='Column break occurs after this box',
                                                    variable=self.program_state.gui_state.tk_current_box_is_line_break, onvalue=True,
                                                    offvalue=False, command=update_line_break, state="disabled")
        self.current_box_image_display.grid(row=0, column=1)

        selection_frame = tk.Frame(self.frame)
        previous_button = tk.Button(selection_frame, text="< Previous", command=self.on_previous, state="disabled",
                                    width=10, underline=0)
        previous_button.grid(row=0, column=0)
        current_box_index_display = tk.Label(selection_frame, height=1, width=10,
                                             textvariable=self.program_state.gui_state.tk_current_box_out_of_current_type,
                                             relief="sunken", state="disabled")
        current_box_index_display.grid(row=0, column=1)
        next_button = tk.Button(selection_frame, text="Next >", command=self.on_next, state="disabled", width=10, underline=5)
        next_button.grid(row=0, column=2)
        selection_frame.grid(row=1, column=1)
        annotations_frame.grid(row=2, column=1)
        self.widgets = [previous_button, current_box_index_display, next_button]

        self.program_state.gui_state.main_window.bind("<Control-Left>", lambda x: previous_button.invoke())
        self.program_state.gui_state.main_window.bind("<Control-Right>", lambda x: next_button.invoke())

        self.box_excluded_checkbox.grid(row=0, column=0, sticky="W")
        self.box_line_break_checkbox.grid(row=1, column=0, sticky="W")

        text_annotations_frame.grid(row=0, column=0)
        box_frames.grid(row=1, column=0)

    def set_mode_properties(self, props: dict):
        if self.musical_annotation_frame is not None:
            self.musical_annotation_frame.set_mode_properties(props)

    def get_mode_properties(self):
        if self.musical_annotation_frame is not None:
            return self.musical_annotation_frame.get_mode_properties()

    def get_frame(self):
        return self.frame
