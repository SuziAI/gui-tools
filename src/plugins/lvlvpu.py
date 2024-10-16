import dataclasses
import json
import pickle
import tkinter as tk
import tkinter.ttk
from tkinter.messagebox import askyesno

import PIL
import numpy as np
import pytesseract
from PIL import ImageTk

from src.auxiliary import BoxType, onedim_cv_to_tkinter_image, open_file_as_tk_image
from src.plugins.lvlvpu_type import ExtendedLvlv
from src.plugins.suzipu_lvlvpu_gongchepu.lvlvpu_intelligent_assistant import load_model, load_transforms, predict_all
from src.plugins.suzipu_lvlvpu_gongchepu.notes_to_image import common_notation_to_jianpu, common_notation_to_staff, \
    notation_to_lvlvpu, NotationResources, write_to_musicxml
from src.programstate import ProgramState
from src.config import CHINESE_FONT_FILE, NO_KUISCIMA_ANNOTATIONS
from src.plugins.suzipu_lvlvpu_gongchepu.common import Symbol, ModeSelectorFrame

EMPTY_ANNOTATION = {"pitch": None}
PLUGIN_NAME = "Lülüpu"
DISPLAY_NOTATION = True
HAS_MUSICXML = True

RESOURCES = NotationResources()


def save_as_musicxml(mode, file_path, music_list, lyrics_list, fingering, title, mode_str, preface):
    new_music_list = []
    for idx, music in enumerate(music_list):

        melody_symbol = None
        is_zhezi = False
        try:
            pitch = music["pitch"]
            if music["pitch"] == ExtendedLvlv.ZHE_ZI:
                is_zhezi = True
                if idx > 0:
                    pitch = music_list[idx - 1]["pitch"]  # Zhezi uses previous pitch
            melody_symbol = ExtendedLvlv.to_gongche_melody_symbol(pitch)
        except (KeyError, TypeError):
            pass

        new_music_list.append({"pitch": melody_symbol, "is_zhezi": is_zhezi})
    write_to_musicxml(file_path, new_music_list, lyrics_list, fingering, title, mode_str, preface)


def notation_to_own(mode, music_list, lyrics_list, line_break_idxs, fingering, return_boxes=False, is_vertical=False):
    new_music_list = []
    for idx, music in enumerate(music_list):

        melody_symbol = None
        is_zhezi = False
        try:
            pitch = music["pitch"]
            if music["pitch"] == ExtendedLvlv.ZHE_ZI:
                is_zhezi = True
                if idx > 0:
                    pitch = music_list[idx - 1]["pitch"]  # Zhezi uses previous pitch
            melody_symbol = ExtendedLvlv.to_gongche_melody_symbol(pitch)
        except (KeyError, TypeError):
            pass

        new_music_list.append({"pitch": melody_symbol, "is_zhezi": is_zhezi})

    return notation_to_lvlvpu(
                    RESOURCES.small_font,
                    RESOURCES.smallest_font,
                    new_music_list, lyrics_list,
                    line_break_idxs,
                    return_boxes,
                    is_vertical)


def notation_to_jianpu(mode, music_list, lyrics_list, line_break_idxs, fingering, return_boxes=False, is_vertical=False):
    new_music_list = []
    for idx, music in enumerate(music_list):

        melody_symbol = None
        is_zhezi = False
        try:
            pitch = music["pitch"]
            if music["pitch"] == ExtendedLvlv.ZHE_ZI:
                is_zhezi = True
                if idx > 0:
                    pitch = music_list[idx-1]["pitch"]  # Zhezi uses previous pitch
            melody_symbol = ExtendedLvlv.to_gongche_melody_symbol(pitch)
        except (KeyError, TypeError):
            pass

        new_music_list.append({"pitch": melody_symbol, "is_zhezi": is_zhezi})
    return common_notation_to_jianpu(RESOURCES.small_font, RESOURCES.jianpu_image_dict, None, new_music_list, lyrics_list, line_break_idxs, fingering, return_boxes)


def notation_to_staff(mode, music_list, lyrics_list, line_break_idxs, fingering, return_boxes=False, is_vertical=False):
    new_music_list = []
    for idx, music in enumerate(music_list):

        melody_symbol = None
        is_zhezi = False
        try:
            pitch = music["pitch"]
            if music["pitch"] == ExtendedLvlv.ZHE_ZI:
                is_zhezi = True
                if idx > 0:
                    pitch = music_list[idx - 1]["pitch"]  # Zhezi uses previous pitch
            melody_symbol = ExtendedLvlv.to_gongche_melody_symbol(pitch)
        except (KeyError, TypeError):
            pass

        new_music_list.append({"pitch": melody_symbol, "is_zhezi": is_zhezi})
    return common_notation_to_staff(RESOURCES.small_font, RESOURCES.staff_image_dict, None, new_music_list, lyrics_list, line_break_idxs, fingering, return_boxes)


class IntelligentAssistantFrame:
    def __init__(self, window_handle, program_state: ProgramState):
        self.frame = tk.Frame(window_handle)  #  tk.LabelFrame(window_handle, text="Intelligent Assistant")  # TODO
        self.state = False
        self.program_state = program_state
        self.empty_image = ImageTk.PhotoImage(image=PIL.Image.new("RGB", (60, 60), (255, 255, 255)))

        self._models = None
        self._transforms = None
        self._predictions = None
        self._prediction_frames = None
        self._notation_annotations = None

        self._widgets = []
        self._create_frame()

    def _create_frame(self):
        prediction_frame = tk.LabelFrame(self.frame, text="Prediction")
        pitch_prediction_frame = tk.Frame(prediction_frame)
        pitch_prediction = [PredictionDisplayFrame(pitch_prediction_frame),
                            PredictionDisplayFrame(pitch_prediction_frame),
                            PredictionDisplayFrame(pitch_prediction_frame)]

        clustering_frame = tk.LabelFrame(self.frame, text="Most Similar")
        pitch_clustering_frame = tk.Frame(clustering_frame)
        pitch_clustering = [PredictionDisplayFrame(pitch_clustering_frame, True),
                            PredictionDisplayFrame(pitch_clustering_frame, True),
                            PredictionDisplayFrame(pitch_clustering_frame, True)]
        for idx, frame in enumerate(pitch_prediction):
            frame.get_frame().grid(row=0, column=idx, padx=10, pady=3)
        for idx, frame in enumerate(pitch_clustering):
            frame.get_frame().grid(row=0, column=idx, padx=10, pady=3)

        pitch_prediction_frame.grid(row=0, column=0, padx=10, pady=3)
        prediction_frame.grid(row=0, column=0, padx=10, pady=3)

        pitch_clustering_frame.grid(row=0, column=0, padx=10, pady=3)
        clustering_frame.grid(row=0, column=1, padx=10, pady=3)

        self._prediction_frames = {"prediction": {"pitch": pitch_prediction},
                                   "similarity": {"pitch": pitch_clustering}}

    def get_frame(self):
        return self.frame

    def set_state(self, boolean):
        self.state = boolean

        for idx in range(3):
            self._prediction_frames["prediction"]["pitch"][idx].set_state(self.state)
            self._prediction_frames["similarity"]["pitch"][idx].set_state(self.state)

    def update(self):
        if self._predictions is not None:
            current_annotation_index = self.program_state.get_current_local_annotation_index()
            if current_annotation_index in self._predictions["empty_idxs"]:
                for idx in range(3):
                    self._prediction_frames["prediction"]["pitch"][idx].set_properties("None", "")
                    self._prediction_frames["similarity"]["pitch"][idx].set_properties(self.empty_image, "", "None")
            else:
                for idx in range(3):
                    pitch_prediction = self._predictions["prediction"]["pitch"][current_annotation_index]
                    self._prediction_frames["prediction"]["pitch"][idx].set_properties(pitch_prediction["annotations"][idx], f"{100*pitch_prediction['confidences'][idx]:.2f}%")

                    pitch_similar = self._predictions["similarity"]["pitch"][current_annotation_index][idx]
                    self._prediction_frames["similarity"]["pitch"][idx].set_properties(pitch_similar["image"], f"{pitch_similar['edition'].upper()} {int(pitch_similar['similarity'])}", pitch_similar['annotation'])

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

        current_box_type = self.program_state.get_current_type() # Must be music type
        self._predictions = predict_all(self.program_state.get_raw_box_images_from_type(current_box_type), self._models, self._transforms, update_window=lambda x: [progress.set(x), win.update()])
        predictions = [(self._predictions["prediction"]["pitch"][box_idx]["annotations"][0]) for box_idx in range(len(self._predictions["prediction"]["pitch"]))]
        for empty_idx in self._predictions["empty_idxs"]:
            predictions[empty_idx] = (None, None)

        self._notation_annotations = [{"pitch": pitch} for pitch in predictions]
        self.update()

        win.destroy()

    def overwrite_all_music_boxes(self):
        self.program_state.fill_all_boxes_of_current_type(self._notation_annotations)


class PredictionDisplayFrame:
    def __init__(self, window_handle, has_second_image=False):
        self.frame = tk.Frame(window_handle)
        self.state = False
        self.has_second_image = has_second_image

        self.image = tk.Label(self.frame, text="None", relief="sunken", state="disabled")
        self.label = tk.Label(self.frame, relief="sunken", width=10 if self.has_second_image else 7)
        self.image.grid(row=0, column=1)
        self.label.grid(row=1, column=1)

        if self.has_second_image:
            self.second_image = tk.Label(self.frame, text="None", relief="sunken", state="disabled")
            self.second_image.grid(row=1, column=0)

    def get_frame(self):
        return self.frame

    def set_state(self, boolean):
        self.state = boolean
        self.image.config(state="normal" if self.state else "disabled")
        self.label.config(state="normal" if self.state else "disabled")
        if self.has_second_image:
            self.second_image.config(state="normal" if self.state else "disabled")

    def set_properties(self, tkimg, label_text, class2=None):
        if isinstance(tkimg, str):
            txt = "None"
            try:
                txt = ExtendedLvlv.to_name(tkimg)
            except Exception:
                pass
            self.image.config(text=txt, font="Arial 20")
        else:
            self.image.config(image=tkimg)
        self.label.config(text=label_text)
        if class2 and self.has_second_image:
            self.second_image.config(text=ExtendedLvlv.to_name(class2), font="Arial 13")


class SymbolDisplayFrame:
    def __init__(self, window_handle):
        self.frame = tk.Frame(window_handle)
        self._create_frame()
        self.state = False

    def _create_frame(self):
        self.display_first_symbol = tk.Label(self.frame,
                                             text="None",
                                             relief="sunken", state="disabled")

        self.display_first_symbol.grid(row=0, column=0)

    def set_state(self, boolean):
        self.state = boolean
        if boolean:
            self.display_first_symbol.config(state="normal")
        else:
            self.display_first_symbol.config(state="disabled")

    def update(self, annotation):
        if self.state:
            try:
                self.display_first_symbol.config(text=ExtendedLvlv.from_class(annotation), font="Arial 20",)
            except Exception:
                self.display_first_symbol.config(text="None")
        else:
            self.display_first_symbol.config(text="None")

    def get_frame(self):
        return self.frame


def predict_lvlv_from_images(image_list, progress, total_progress, update=lambda: None):
    char_whitelist = '''清黃大太夹姑仲蕤林夷南無應折字'''
    tesseract_config = f'''--psm 10 -c tessedit_char_whitelist={char_whitelist} --tessdata-dir "./weights"'''
    output = []

    for num, img in enumerate(image_list):
        img = np.asarray(img)
        try:
            prediction = pytesseract.image_to_string(img, lang="chi_tra", config=tesseract_config)
        except pytesseract.pytesseract.TesseractError as error:
            print("\n\n Error: Need to install tesseract chi_tra. Refer to README.md to install.")
            print(error)
            return None

        if prediction == "\x0c" or len(prediction) == 0:
            prediction = " "


        try:
            lvlv = ExtendedLvlv.from_name(prediction.strip())
        except KeyError:
            lvlv = None
        output.append(lvlv)

        new_progress = progress.get()/100 * total_progress
        progress.set(100*(new_progress+1)/total_progress)
        update()
    return output


def exec_intelligent_fill_window_text(get_box_images):
    quick_fill_window = tk.Toplevel()

    exit_save_var = tk.BooleanVar()
    exit_save_var.set(False)

    prediction = tk.StringVar()

    def on_predict():
        exit_save_var.set(True)
        image_list = get_box_images(BoxType.MUSIC)


        total_progress = len(image_list)

        progress = tk.DoubleVar(value=0)

        def predict(update):
            prediction.set(json.dumps(predict_lvlv_from_images(image_list, progress, total_progress, update)))

            if not prediction:
                exit_save_var.set(False)

        def wait(message):
            win = tk.Toplevel()
            win.title('Wait')
            tk.Label(win, text=message, padx=10, pady=10).pack()
            tkinter.ttk.Progressbar(win, length=100, orient=tk.HORIZONTAL, variable=progress).pack(pady=10)
            return win

        win = wait("Intelligent lülüpu prediction in progress.")
        quick_fill_window.wait_visibility(win)
        win.update()

        predict(update=win.update)
        win.destroy()

        quick_fill_window.destroy()

    quick_fill_window.title(f"Intelligent Fill")

    tk.Label(quick_fill_window, padx=10, pady=10, text=f"Intelligent Fill tries to recognize the lülüpu from all boxes containing musical data.\nIt might take a while, and all musical content is overwritten.\nProceed?").pack()

    button_frame = tk.Frame(quick_fill_window)
    tk.Button(button_frame, text="OK", command=on_predict).grid(column=0, row=0)
    tk.Button(button_frame, text="Cancel", command=quick_fill_window.destroy).grid(column=1, row=0)
    button_frame.pack()

    quick_fill_window.wait_window()

    return exit_save_var.get(), json.loads(prediction.get())


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
        self.lvlv_list = [ExtendedLvlv.to_name(lvlv) for lvlv in dataclasses.astuple(ExtendedLvlv())]

        self.window_handle = window_handle
        self.program_state = program_state
        self.frame = tk.Frame(self.window_handle)
        self.mode_selector = None
        self.symbol_display = None
        self.musical_var = tk.StringVar(self.frame, "None")
        self.simple = simple
        self._widgets = []
        self._create_frame()
        self.intelligent_assistant_frame = None

        def get_reference_images():
            with open("./src/plugins/suzipu_lvlvpu_gongchepu/suzi_lvlv_jianzi_references.pkl", "rb") as file_handle:
                obj = pickle.load(file_handle)
                for key in obj.keys():
                    for key2 in obj[key].keys():
                        obj[key][key2] = onedim_cv_to_tkinter_image(obj[key][key2])
                return obj
        self.reference_images = get_reference_images()
        self.canvas = None
        self._image = None
        self.no_annotations_image = open_file_as_tk_image(NO_KUISCIMA_ANNOTATIONS)

    def update_display(self):
        annotation = self.program_state.get_current_annotation()

        if self.intelligent_assistant_frame:
            self.intelligent_assistant_frame.update()

        if self.canvas:
            try:
                self.canvas.delete('all')
                self._image = self.reference_images["Lvlvpu"][str(annotation)]
                self.canvas.yview_moveto(0)
            except Exception as e:
                print(e)
                self._image = self.no_annotations_image
            image_on_canvas = self.canvas.create_image(0, 0, image=self._image, anchor="nw")
            self.canvas.config(width=600,
                               height=500)

        if annotation is not None:
            try:
                self.musical_var.set(ExtendedLvlv.to_name(annotation["pitch"]))
            except Exception:
                self.musical_var.set("None")
        else:
            self.musical_var.set("None")

    def _create_frame(self):
        self.mode_selector = ModeSelectorFrame(self.frame, mode_variable=self.program_state.gui_state.tk_current_mode_string, on_get_mode_string=self.program_state.get_mode_string)

        mode_selector_frame = self.mode_selector.get_frame()
        annotator_frame = tk.Frame(self.frame)
        intelligent_frame = tk.Frame(self.frame)

        def update_annotation(*args):
            def return_none_if_none(string):
                if string == "None":
                    return None
                return string
            try:
                annotation = {"pitch": return_none_if_none(ExtendedLvlv.from_name(self.musical_var.get()))}
            except Exception:
                annotation = EMPTY_ANNOTATION
            self.program_state.set_current_annotation(annotation)

        def on_intelligent_assistant():
            intelligent_assistant_window = tk.Toplevel(self.frame)
            intelligent_assistant_window.title("Chinese Musical Annotation Tool - Suzipu Intelligent Assistant")

            canvas_frame = tk.LabelFrame(intelligent_assistant_window, text="KuiSCIMA Instances With Same Annotation")
            self.canvas = tk.Canvas(canvas_frame, relief="sunken", state="disabled")
            vbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
            vbar.pack(side=tk.RIGHT, fill=tk.BOTH)
            vbar.config(command=self.canvas.yview)
            self.canvas.config(yscrollcommand=vbar.set)
            self.canvas.pack(padx=5, pady=5)

            def onFrameConfigure(event):
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))

            canvas_frame.bind("<Configure>", onFrameConfigure)

            omr_frame = tk.LabelFrame(intelligent_assistant_window, text="Optical Music Recognition")
            self.intelligent_assistant_frame = IntelligentAssistantFrame(omr_frame, self.program_state)
            self.intelligent_assistant_frame.set_state(True)

            int_buttons_frame = tk.Frame(omr_frame)

            def on_click_predict():
                self.intelligent_assistant_frame.predict()
                self.intelligent_assistant_frame.update()
                self.update_display()
                overwrite_button.config(state="normal")

            def on_overwrite():
                make_prediction = askyesno("Overwrite Annotations - Proceed",
                                           message="All the annotations will be overwritten with the model predictions. The original annotations will be lost.\nProceed?")
                if make_prediction:
                    self.intelligent_assistant_frame.overwrite_all_music_boxes()
                    self.update_display()

            tk.Button(int_buttons_frame, text="Predict", command=on_click_predict).grid(row=0, column=0)
            overwrite_button = tk.Button(int_buttons_frame, text="Overwrite Annotations with Predictions",
                                         state="disabled", command=on_overwrite)
            overwrite_button.grid(row=0, column=1)

            int_buttons_frame.pack()
            self.intelligent_assistant_frame.get_frame().pack()

            omr_frame.pack(padx=5, pady=5)
            canvas_frame.pack(padx=5, pady=5)

            self.update_display()

        def on_quick_fill():
            exit_save_var, text_variable = exec_quick_fill_window(self.program_state.gui_state.tk_current_boxtype, self.program_state.gui_state.tk_num_all_boxes_of_current_type)
            if exit_save_var:
                self.program_state.fill_all_boxes_of_current_type(json.loads(text_variable))

        def construct_lvlvpu_frame(frame, primary=True):
            symbol_frame = tk.Frame(frame)

            none_button = tk.Radiobutton(symbol_frame,
                                         variable=self.musical_var,
                                         text="", font="Arial 13",
                                         width=4,
                                         height=2,
                                         value="", indicator=0, command=update_annotation)
            zhezi_button = tk.Radiobutton(symbol_frame,
                                          variable=self.musical_var,
                                          text="字折", font="Arial 13",
                                          width=4,
                                          height=2,
                                          value=ExtendedLvlv.to_name(ExtendedLvlv.ZHE_ZI), indicator=0, command=update_annotation)
            none_button.grid(row=0, column=0)
            zhezi_button.grid(row=0, column=1)
            self._widgets.append(none_button)
            self._widgets.append(zhezi_button)

            for idx, melody_var in enumerate(self.lvlv_list[0:12]):
                current_button = tk.Radiobutton(symbol_frame,
                                                variable=self.musical_var,
                                                text=melody_var, font="Arial 13",
                                                width=4,
                                                height=2,
                                                value=melody_var, indicator=0, command=update_annotation)
                current_button.grid(row=1, column=idx)
                self._widgets.append(current_button)
            for idx, melody_var in enumerate(self.lvlv_list[12:-1]):
                current_button = tk.Radiobutton(symbol_frame,
                                                variable=self.musical_var,
                                                text=melody_var, font="Arial 13",
                                                width=4,
                                                height=2,
                                                value=melody_var, indicator=0, command=update_annotation)
                current_button.grid(row=2, column=idx)
                self._widgets.append(current_button)
            return symbol_frame

        button_frame = tk.Frame(self.frame)

        symbol_frames = tk.Frame(annotator_frame)
        symbol_display = tk.Label(annotator_frame, textvariable=self.musical_var, relief="sunken", font="Arial 13", width=4, height=2)
        symbol_display.pack()
        self._widgets.append(symbol_display)
        construct_lvlvpu_frame(symbol_frames, True).grid(sticky="W", row=0, column=0, padx=10, pady=4)

        symbol_display.grid(row=0, column=0, padx=5)
        symbol_frames.grid(row=0, column=1)

        if not self.simple:
            quick_fill_button = tk.Button(intelligent_frame, text="Quick Fill...", command=on_quick_fill)
            quick_fill_button.grid(row=0, column=0)
            intelligent_button = tk.Button(intelligent_frame, text="Intelligent Assistant...", command=on_intelligent_assistant)
            intelligent_button.grid(row=0, column=1)
            self._widgets.append(intelligent_button)
            self._widgets.append(quick_fill_button)

        mode_selector_frame.grid(row=0, column=0)
        annotator_frame.grid(row=1, column=0)
        button_frame.grid(row=2, column=0)
        intelligent_frame.grid(row=3, column=0)

    def get_frame(self):
        return self.frame

    def set_state(self, boolean):
        if boolean:
            state = "normal"
        else:
            state = "disabled"

        for widget in self._widgets:
            widget.config(state=state)
        self.mode_selector.set_state(boolean)

    def set_mode_properties(self, props: dict):
        self.mode_selector.set_properties(props)

    def get_mode_properties(self):
        return self.mode_selector.get_properties()