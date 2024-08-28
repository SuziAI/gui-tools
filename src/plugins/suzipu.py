import dataclasses
import json
import tkinter as tk
import tkinter.ttk
from tkinter.messagebox import askyesno

import PIL
from PIL import ImageTk

from src.auxiliary import BoxType
from src.plugins.suzipu_lvlvpu_gongchepu.notes_to_image import common_notation_to_jianpu, common_notation_to_staff, \
    notation_to_suzipu, NotationResources
from src.plugins.suzipu_lvlvpu_gongchepu.suzipu_intelligent_assistant import load_model, load_transforms, predict_all
from src.programstate import ProgramState
from src.config import CHINESE_FONT_FILE
from src.plugins.suzipu_lvlvpu_gongchepu.common import Symbol, SuzipuMelodySymbol, SuzipuAdditionalSymbol, \
    _create_suzipu_images, ModeSelectorFrame


EMPTY_ANNOTATION = {"pitch": None, "secondary": None}
PLUGIN_NAME = "Suzipu"
DISPLAY_NOTATION = True

RESOURCES = NotationResources()


def notation_to_own(mode, music_list, lyrics_list, line_break_idxs, fingering, return_boxes=False, is_vertical=False):
    return notation_to_suzipu(
                    RESOURCES.small_font,
                    RESOURCES.suzipu_image_dict,
                    music_list, lyrics_list,
                    line_break_idxs,
                    return_boxes,
                    is_vertical)


def notation_to_jianpu(mode, music_list, lyrics_list, line_break_idxs, fingering, return_boxes=False, is_vertical=False):
    return common_notation_to_jianpu(RESOURCES.small_font, RESOURCES.jianpu_image_dict, mode, music_list, lyrics_list, line_break_idxs, fingering, return_boxes)


def notation_to_staff(mode, music_list, lyrics_list, line_break_idxs, fingering, return_boxes=False, is_vertical=False):
    return common_notation_to_staff(RESOURCES.small_font, RESOURCES.staff_image_dict, mode, music_list, lyrics_list, line_break_idxs, fingering, return_boxes)


class IntelligentAssistantFrame:
    def __init__(self, window_handle, program_state: ProgramState, button_images):
        self.frame = tk.Frame(window_handle)  #  tk.LabelFrame(window_handle, text="Intelligent Assistant")  # TODO
        self.state = False
        self.program_state = program_state
        self.button_images = button_images
        self.empty_image = ImageTk.PhotoImage(image=PIL.Image.new("RGB", (60, 60), (255, 255, 255)))

        self._models = None
        self._transforms = None
        self._predictions = None
        self._prediction_frames = None

        self._widgets = []
        self._create_frame()

    def _create_frame(self):
        prediction_frame = tk.LabelFrame(self.frame, text="Prediction")
        pitch_prediction_frame = tk.LabelFrame(prediction_frame, text="Pitch")
        pitch_prediction = [PredictionDisplayFrame(pitch_prediction_frame, self.button_images),
                            PredictionDisplayFrame(pitch_prediction_frame, self.button_images),
                            PredictionDisplayFrame(pitch_prediction_frame, self.button_images)]
        secondary_prediction_frame = tk.LabelFrame(prediction_frame, text="Secondary")
        secondary_prediction = [PredictionDisplayFrame(secondary_prediction_frame, self.button_images),
                                PredictionDisplayFrame(secondary_prediction_frame, self.button_images),
                                PredictionDisplayFrame(secondary_prediction_frame, self.button_images)]

        clustering_frame = tk.LabelFrame(self.frame, text="Most Similar")
        pitch_clustering_frame = tk.LabelFrame(clustering_frame, text="Pitch")
        pitch_clustering = [PredictionDisplayFrame(pitch_clustering_frame, self.button_images, True),
                            PredictionDisplayFrame(pitch_clustering_frame, self.button_images, True),
                            PredictionDisplayFrame(pitch_clustering_frame, self.button_images, True)]
        secondary_clustering_frame = tk.LabelFrame(clustering_frame, text="Secondary")
        secondary_clustering = [PredictionDisplayFrame(secondary_clustering_frame, self.button_images, True),
                                PredictionDisplayFrame(secondary_clustering_frame, self.button_images, True),
                                PredictionDisplayFrame(secondary_clustering_frame, self.button_images, True)]
        for idx, frame in enumerate(pitch_prediction):
            frame.get_frame().grid(row=0, column=idx, padx=10, pady=3)
        for idx, frame in enumerate(secondary_prediction):
            frame.get_frame().grid(row=0, column=idx, padx=10, pady=3)
        for idx, frame in enumerate(pitch_clustering):
            frame.get_frame().grid(row=0, column=idx, padx=10, pady=3)
        for idx, frame in enumerate(secondary_clustering):
            frame.get_frame().grid(row=0, column=idx, padx=10, pady=3)

        pitch_prediction_frame.grid(row=0, column=0, padx=10, pady=3)
        secondary_prediction_frame.grid(row=1, column=0, padx=10, pady=3)
        prediction_frame.grid(row=0, column=0, padx=10, pady=3)

        pitch_clustering_frame.grid(row=0, column=0, padx=10, pady=3)
        secondary_clustering_frame.grid(row=1, column=0, padx=10, pady=3)
        clustering_frame.grid(row=0, column=1, padx=10, pady=3)

        self._prediction_frames = {"prediction": {"pitch": pitch_prediction, "secondary": secondary_prediction},
                                   "similarity": {"pitch": pitch_clustering, "secondary": secondary_clustering}}

    def get_frame(self):
        return self.frame

    def set_state(self, boolean):
        self.state = boolean

        for idx in range(3):
            self._prediction_frames["prediction"]["pitch"][idx].set_state(self.state)
            self._prediction_frames["prediction"]["secondary"][idx].set_state(self.state)
            self._prediction_frames["similarity"]["pitch"][idx].set_state(self.state)
            self._prediction_frames["similarity"]["secondary"][idx].set_state(self.state)

    def update(self):
        if self._predictions is not None:
            current_annotation_index = self.program_state.get_current_local_annotation_index()
            if current_annotation_index in self._predictions["empty_idxs"]:
                for idx in range(3):
                    self._prediction_frames["prediction"]["pitch"][idx].set_properties(
                        self.button_images[None],
                        "")
                    self._prediction_frames["prediction"]["secondary"][idx].set_properties(
                        self.button_images[None],
                        "")
                    self._prediction_frames["similarity"]["pitch"][idx].set_properties(self.empty_image, "", self.button_images[None])
                    self._prediction_frames["similarity"]["secondary"][idx].set_properties(self.empty_image, "", self.button_images[None])
            else:
                for idx in range(3):
                    pitch_prediction = self._predictions["prediction"]["pitch"][current_annotation_index]
                    secondary_prediction = self._predictions["prediction"]["secondary"][current_annotation_index]
                    self._prediction_frames["prediction"]["pitch"][idx].set_properties(self.button_images[pitch_prediction["annotations"][idx]], f"{100*pitch_prediction['confidences'][idx]:.2f}%")
                    self._prediction_frames["prediction"]["secondary"][idx].set_properties(self.button_images[secondary_prediction["annotations"][idx]], f"{100*secondary_prediction['confidences'][idx]:.2f}%")

                    pitch_similar = self._predictions["similarity"]["pitch"][current_annotation_index][idx]
                    secondary_similar = self._predictions["similarity"]["secondary"][current_annotation_index][idx]
                    self._prediction_frames["similarity"]["pitch"][idx].set_properties(pitch_similar["image"], f"{pitch_similar['edition'].upper()} {int(pitch_similar['similarity'])}", self.button_images[pitch_similar['annotation']])
                    self._prediction_frames["similarity"]["secondary"][idx].set_properties(secondary_similar["image"], f"{secondary_similar['edition'].upper()} {int(secondary_similar['similarity'])}", self.button_images[secondary_similar['annotation']])

    def predict(self):
        progress = tk.IntVar(value=0)

        def wait(message):
            win = tk.Toplevel()
            win.title('Wait')
            tk.Label(win, text=message, padx=10, pady=10).pack()
            tk.ttk.Progressbar(win, length=100, orient=tk.HORIZONTAL, variable=progress).pack(pady=10)
            return win

        win = wait("Intelligent assistant prediction in progress.")
        self.frame.wait_visibility(win)
        win.update()

        if self._models is None or self._transforms is None:
            self._models = load_model()
            self._transforms = load_transforms()
            progress.set(50)
            win.update()
        else:
            progress.set(50)
            win.update()

        self._predictions = predict_all(self.program_state.get_raw_box_images_from_type(BoxType.MUSIC), self._models, self._transforms, update_window=lambda x: [progress.set(x), win.update()])
        predictions = [(self._predictions["prediction"]["pitch"][box_idx]["annotations"][0], self._predictions["prediction"]["secondary"][box_idx]["annotations"][0]) for box_idx in range(len(self._predictions["prediction"]["secondary"]))]
        for empty_idx in self._predictions["empty_idxs"]:
            predictions[empty_idx] = (None, None)
        notation_annotations = [{"pitch": pitch, "secondary": secondary} for pitch, secondary in predictions]

        self.program_state.fill_all_boxes_of_current_type(notation_annotations)
        self.update()

        win.destroy()


class PredictionDisplayFrame:
    def __init__(self, window_handle, button_images, has_second_image=False):
        self.frame = tk.Frame(window_handle)
        self._button_images = button_images
        self.state = False
        self.has_second_image = has_second_image

        self.image = tk.Label(self.frame, image=self._button_images[Symbol.NONE], relief="sunken", state="disabled")
        self.label = tk.Label(self.frame, relief="sunken", width=10 if self.has_second_image else 7)
        self.image.grid(row=0, column=1)
        self.label.grid(row=1, column=1)

        if self.has_second_image:
            self.second_image = tk.Label(self.frame, image=self._button_images[Symbol.NONE], relief="sunken", state="disabled")
            self.second_image.grid(row=1, column=0)

    def get_frame(self):
        return self.frame

    def set_state(self, boolean):
        self.state = boolean
        self.image.config(state="normal" if self.state else "disabled")
        self.label.config(state="normal" if self.state else "disabled")
        if self.has_second_image:
            self.second_image.config(state="normal" if self.state else "disabled")

    def set_properties(self, tkimage, label_text, tkimage2=None):
        self.image.config(image=tkimage)
        self.label.config(text=label_text)
        if tkimage2 and self.has_second_image:
            self.second_image.config(image=tkimage2)


class SymbolDisplayFrame:
    def __init__(self, window_handle, button_images):
        self.frame = tk.Frame(window_handle)
        self._button_images = button_images
        self._create_frame()
        self.state = False

    def _create_frame(self):
        self.display_first_symbol = tk.Label(self.frame,
                                             image=self._button_images[Symbol.NONE],
                                             relief="sunken", state="disabled")
        self.display_second_symbol = tk.Label(self.frame,
                                              image=self._button_images[Symbol.NONE],
                                              relief="sunken", state="disabled")

        self.display_first_symbol.grid(row=0, column=0)
        self.display_second_symbol.grid(row=1, column=0)

    def set_state(self, boolean):
        self.state = boolean
        if boolean:
            self.display_first_symbol.config(state="normal")
            self.display_second_symbol.config(state="normal")
        else:
            self.display_first_symbol.config(state="disabled")
            self.display_second_symbol.config(state="disabled")

    def update(self, annotation):
        if self.state:
            try:
                self.display_first_symbol.config(image=self._button_images[annotation["pitch"]])
                self.display_second_symbol.config(image=self._button_images[annotation["secondary"]])
            except Exception:
                self.display_first_symbol.config(image=self._button_images["None"])
                self.display_second_symbol.config(image=self._button_images["None"])
        else:
            self.display_first_symbol.config(image=self._button_images["None"])
            self.display_second_symbol.config(image=self._button_images["None"])

    def get_frame(self):
        return self.frame


def exec_quick_fill_window(annotation_type_var, max_length_var):
    quick_fill_window = tk.Toplevel()

    exit_save_var = tk.BooleanVar()
    exit_save_var.set(False)
    def on_destroy_save_changes():
        exit_save_var.set(True)
        quick_fill_window.destroy()

    annotation_type = annotation_type_var.get()

    quick_fill_window.title(f"Quick Fill {annotation_type}")

    text_variable = tk.StringVar(quick_fill_window)
    text_variable.set("")

    left_character_string = tk.StringVar(quick_fill_window)
    left_character_string.set("")
    ok_button = tk.Button(quick_fill_window, text="OK", command=on_destroy_save_changes, state="normal")

    tk.Entry(quick_fill_window, font=CHINESE_FONT_FILE,
             textvariable=text_variable).pack()
    tk.Label(quick_fill_window, textvariable=left_character_string).pack()
    ok_button.pack()

    quick_fill_window.wait_window()

    return exit_save_var.get(), text_variable.get()


class NotationAnnotationFrame:
    def __init__(self, window_handle, program_state: ProgramState, simple=False):
        self.window_handle = window_handle
        self.program_state = program_state
        self.simple = simple

        self.frame = tk.Frame(self.window_handle)

        self.mode_selector = None
        self._button_images = _create_suzipu_images()

        self.symbol_display = None
        self.intelligent_assistant_frame = None

        self.first_musical_var = tk.StringVar(self.frame, "None")
        self.second_musical_var = tk.StringVar(self.frame, "None")

        self._widgets = []

        self._create_frame()

    def update_display(self):
        annotation = self.program_state.get_current_annotation()
        self.symbol_display.update(annotation)
        self.intelligent_assistant_frame.update()

        if annotation is not None:
            try:
                self.first_musical_var.set(annotation["pitch"])
                self.second_musical_var.set(annotation["secondary"])
            except Exception:
                self.first_musical_var.set("None")
                self.second_musical_var.set("None")
        else:
            self.first_musical_var.set("None")
            self.second_musical_var.set("None")

    def _create_frame(self):
        self.mode_selector = ModeSelectorFrame(self.frame, mode_variable=self.program_state.gui_state.tk_current_mode_string, on_get_mode_string=self.program_state.get_mode_string)

        mode_selector_frame = self.mode_selector.get_frame()
        annotator_frame = tk.Frame(self.frame)

        self.symbol_display = SymbolDisplayFrame(annotator_frame, self._button_images)
        self.intelligent_assistant_frame = IntelligentAssistantFrame(self.frame, self.program_state, self._button_images)

        def update_annotation(*args):
            def return_none_if_none(string):
                if string == "None":
                    return None
                return string

            annotation = {"pitch": return_none_if_none(self.first_musical_var.get()), "secondary": return_none_if_none(self.second_musical_var.get())}
            self.program_state.set_current_annotation(annotation)
            self.update_display()

        def construct_suzipu_frame(frame, musical_var, primary=True):
            prefix = "Pitch" if primary else "Secondary"
            symbol_frame = tk.LabelFrame(frame, text=f"{prefix} Symbol")

            none_button = tk.Radiobutton(symbol_frame, image=self._button_images[Symbol.NONE],
                                         variable=musical_var,
                                         value="None", indicator=0, state="disabled",
                                         command=update_annotation)
            none_button.grid(row=0, column=0)
            self._widgets.append(none_button)

            if primary:
                for idx, melody_var in enumerate(dataclasses.astuple(SuzipuMelodySymbol())):
                    current_button = tk.Radiobutton(symbol_frame, image=self._button_images[melody_var],
                                                    variable=musical_var,
                                                    value=melody_var, indicator=0, state="disabled",
                                                    command=update_annotation)
                    self._widgets.append(current_button)
                    current_button.grid(row=0, column=idx+1)
            else:
                for idx, additional_var in enumerate(dataclasses.astuple(SuzipuAdditionalSymbol())):
                    current_button = tk.Radiobutton(symbol_frame, image=self._button_images[additional_var],
                                                    variable=musical_var,
                                                    value=additional_var, indicator=0, state="disabled",
                                                    command=update_annotation)
                    self._widgets.append(current_button)
                    current_button.grid(row=0, column=idx+1)
            return symbol_frame

        def on_quick_fill():
            exit_save_var, text_variable = exec_quick_fill_window(self.program_state.gui_state.tk_current_boxtype,
                                                                  self.program_state.gui_state.tk_num_all_boxes_of_current_type)
            if exit_save_var:
                self.program_state.fill_all_boxes_of_current_type(json.loads(text_variable))

        def on_intelligent_assistant():
            make_prediction = askyesno("Intelligent Assistant - Proceed", message="Intelligent Assistant tries to automatically recognize the notation in the boxes.\nIt might take some time, and it overwrites all contents of MUSIC boxes.\nProceed?")
            if make_prediction:
                self.intelligent_assistant_frame.predict()
                self.intelligent_assistant_frame.get_frame().grid(row=3, column=0, padx=10, pady=4)
                self.intelligent_assistant_frame.update()
                self.intelligent_assistant_frame.set_state(True)
                self.update_display()

        button_frame = tk.Frame(self.frame)
        quick_fill_button = tk.Button(button_frame, text="Quick Fill...", command=on_quick_fill, state="disabled")
        intelligent_assistant_button = tk.Button(button_frame, text="Intelligent Assistant...", command=on_intelligent_assistant, state="disabled")

        if not self.simple:
            quick_fill_button.grid(row=0, column=0)
            intelligent_assistant_button.grid(row=0, column=1)
            self._widgets += [quick_fill_button, intelligent_assistant_button]

        symbol_frames = tk.Frame(annotator_frame)
        construct_suzipu_frame(symbol_frames, self.first_musical_var, True).grid(sticky="W", row=0, column=0, padx=10, pady=4)  # upper frame
        construct_suzipu_frame(symbol_frames, self.second_musical_var, False).grid(sticky="W", row=1, column=0, padx=10, pady=4, columnspan=2)  # lower frame

        self.symbol_display.get_frame().grid(row=0, column=0)
        symbol_frames.grid(row=0, column=1)

        mode_selector_frame.grid(row=0, column=0)
        annotator_frame.grid(row=1, column=0)
        button_frame.grid(row=2, column=0)

    def get_frame(self):
        return self.frame

    def set_state(self, boolean):
        if boolean:
            state = "normal"
        else:
            state = "disabled"
            self.intelligent_assistant_frame.get_frame().grid_forget()

        for widget in self._widgets:
            widget.config(state=state)
        self.symbol_display.set_state(boolean)
        self.mode_selector.set_state(boolean)

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