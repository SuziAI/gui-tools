import dataclasses
import json
import tkinter as tk
import tkinter.ttk
from tkinter.messagebox import askyesno

import PIL
import numpy as np
import pytesseract
from PIL import ImageTk

from src.auxiliary import BoxType
from src.plugins.suzipu_lvlvpu_gongchepu.notes_to_image import common_notation_to_jianpu, common_notation_to_staff, \
    notation_to_lvlvpu, NotationResources
from src.programstate import ProgramState
from src.config import CHINESE_FONT_FILE
from src.plugins.suzipu_lvlvpu_gongchepu.common import Symbol, SuzipuMelodySymbol, SuzipuAdditionalSymbol, \
    _create_suzipu_images, ModeSelectorFrame, Lvlv, GongcheMelodySymbol


EMPTY_ANNOTATION = {"pitch": None}
PLUGIN_NAME = "Lülüpu"
DISPLAY_NOTATION = True

RESOURCES = NotationResources()


def notation_to_own(mode, music_list, lyrics_list, line_break_idxs, fingering, return_boxes, is_vertical):
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


@dataclasses.dataclass
class ExtendedLvlv:
    HUANGZHONG: str = "HUANGZHONG"
    DALV: str = "DALV"
    TAICU: str = "TAICU"
    JIAZHONG: str = "JIAZHONG"
    GUXIAN: str = "GUXIAN"
    ZHONGLV: str = "ZHONGLV"
    RUIBIN: str = "RUIBIN"
    LINZHONG: str = "LINZHONG"
    YIZE: str = "YIZE"
    NANLV: str = "NANLV"
    WUYI: str = "WUYI"
    YINGZHONG: str = "YINGZHONG"
    HUANGZHONG_QING: str = "HUANGZHONG_QING"
    DALV_QING: str = "DALV_QING"
    TAICU_QING: str = "TAICU_QING"
    JIAZHONG_QING: str = "JIAZHONG_QING"
    ZHE_ZI: str = "ZHE_ZI"

    @classmethod
    def to_gongche_melody_symbol(cls, lvlv):
        return {
            cls.HUANGZHONG: GongcheMelodySymbol.HE,
            cls.DALV: GongcheMelodySymbol.XIA_SI,
            cls.TAICU: GongcheMelodySymbol.SI,
            cls.JIAZHONG: GongcheMelodySymbol.XIA_YI,
            cls.GUXIAN: GongcheMelodySymbol.YI,
            cls.ZHONGLV: GongcheMelodySymbol.SHANG,
            cls.RUIBIN: GongcheMelodySymbol.GOU,
            cls.LINZHONG: GongcheMelodySymbol.CHE,
            cls.YIZE: GongcheMelodySymbol.XIA_GONG,
            cls.NANLV: GongcheMelodySymbol.GONG,
            cls.WUYI: GongcheMelodySymbol.XIA_FAN,
            cls.YINGZHONG: GongcheMelodySymbol.FAN,
            cls.HUANGZHONG_QING: GongcheMelodySymbol.LIU,
            cls.DALV_QING: GongcheMelodySymbol.XIA_WU,
            cls.TAICU_QING: GongcheMelodySymbol.WU,
            cls.JIAZHONG_QING: GongcheMelodySymbol.GAO_WU
        }[lvlv]

    @classmethod
    def to_name(cls, lvlv):
        return {
            cls.HUANGZHONG: "黃",
            cls.DALV: "大",
            cls.TAICU: "太",
            cls.JIAZHONG: "夾",
            cls.GUXIAN: "姑",
            cls.ZHONGLV: "仲",
            cls.RUIBIN: "蕤",
            cls.LINZHONG: "林",
            cls.YIZE: "夷",
            cls.NANLV: "南",
            cls.WUYI: "無",
            cls.YINGZHONG: "應",
            cls.HUANGZHONG_QING: "清黃",
            cls.DALV_QING: "清大",
            cls.TAICU_QING: "清太",
            cls.JIAZHONG_QING: "清夹",
            cls.ZHE_ZI: "字折",
        }[lvlv]

    @classmethod
    def from_name(cls, lvlv):
        return {
            "黃": cls.HUANGZHONG,
            "大": cls.DALV,
            "太": cls.TAICU,
            "夾": cls.JIAZHONG,
            "姑": cls.GUXIAN,
            "仲": cls.ZHONGLV,
            "蕤": cls.RUIBIN,
            "林": cls.LINZHONG,
            "夷": cls.YIZE,
            "南": cls.NANLV,
            "無": cls.WUYI,
            "應": cls.YINGZHONG,
            "清黃": cls.HUANGZHONG_QING,
            "清大": cls.DALV_QING,
            "清太": cls.TAICU_QING,
            "清夹": cls.JIAZHONG_QING,
            "字折": cls.ZHE_ZI,
        }[lvlv]


def predict_lvlv_from_images(image_list, progress, total_progress, update=lambda: None):
    char_whitelist = '''清黃大太夹姑仲蕤林夷南無應'''
    tesseract_config = f'''--psm 10 -c tessedit_char_whitelist={char_whitelist} --tessdata-dir "./weights"'''
    output = []

    for num, img in enumerate(image_list):
        img = np.asarray(img)
        try:
            prediction = pytesseract.image_to_string(img, lang="chi_tra", config=tesseract_config)[0]
        except pytesseract.pytesseract.TesseractError as error:
            print("\n\n Error: Need to install tesseract chi_tra. Refer to README.md to install.")
            print(error)
            return None

        if prediction == "\x0c":
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

    def update_display(self):
        annotation = self.program_state.get_current_annotation()
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

        def on_intelligent_fill():
            exit_save_var, prediction = exec_intelligent_fill_window_text(self.program_state.get_box_images_from_type)
            if exit_save_var:
                if prediction:
                    self.program_state.fill_all_boxes_of_type(BoxType.MUSIC, [{"pitch": p} for p in prediction])

        def on_quick_fill():
            exit_save_var, text_variable = exec_quick_fill_window(self.program_state.gui_state.tk_current_boxtype, self.program_state.gui_state.tk_num_all_boxes_of_current_type)
            if exit_save_var:
                self.program_state.fill_all_boxes_of_current_type(json.loads(text_variable))

        def construct_lvlvpu_frame(frame, primary=True):
            prefix = "Pitch" if primary else "Secondary"
            symbol_frame = tk.LabelFrame(frame, text=f"{prefix} Symbol")

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
            intelligent_button = tk.Button(intelligent_frame, text="Intelligent Assistant...", command=on_intelligent_fill)
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