import dataclasses
import json
import tkinter as tk
import tkinter.ttk
from tkinter.messagebox import askyesno

import PIL
from PIL import ImageTk

from src.auxiliary import BoxType
from src.plugins.suzipu_lvlvpu_gongchepu.notes_to_image import common_notation_to_jianpu, common_notation_to_western
from src.plugins.suzipu_lvlvpu_gongchepu.suzipu_intelligent_assistant import load_model, load_transforms, predict_all
from src.programstate import ProgramState
from src.config import CHINESE_FONT_FILE
from src.plugins.suzipu_lvlvpu_gongchepu.common import Symbol, SuzipuMelodySymbol, SuzipuAdditionalSymbol, \
    _create_suzipu_images, ModeSelectorFrame, Lvlv, GongcheMelodySymbol


EMPTY_ANNOTATION = {"pitch": None}
PLUGIN_NAME = "Lülüpu"
DISPLAY_NOTATION = True


def notation_to_jianpu(font, image_dict, mode, music_list, lyrics_list, line_break_idxs, fingering, return_boxes=False):
    new_music_list = []
    for music in music_list:

        melody_symbol = None
        try:
            melody_symbol = ExtendedLvlv.to_gongche_melody_symbol(music["pitch"])
        except KeyError:
            pass

        new_music_list.append({"pitch": melody_symbol})
    return common_notation_to_jianpu(font, image_dict, None, new_music_list, lyrics_list, line_break_idxs, fingering, return_boxes)


def notation_to_western(font, image_dict, mode, music_list, lyrics_list, line_break_idxs, fingering, return_boxes=False):
    new_music_list = []
    for music in music_list:

        melody_symbol = None
        try:
            melody_symbol = ExtendedLvlv.to_gongche_melody_symbol(music["pitch"])
        except KeyError:
            pass

        new_music_list.append({"pitch": melody_symbol})
    return common_notation_to_western(font, image_dict, None, new_music_list, lyrics_list, line_break_idxs, fingering, return_boxes)


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
    QING_HUANGZHONG: str = "QING_HUANGZHONG"
    QING_DALV: str = "QING_DALV"
    QING_TAICU: str = "QING_TAICU"
    QING_JIAZHONG: str = "QING_JIAZHONG"

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
            cls.QING_HUANGZHONG: GongcheMelodySymbol.LIU,
            cls.QING_DALV: GongcheMelodySymbol.XIA_WU,
            cls.QING_TAICU: GongcheMelodySymbol.WU,
            cls.QING_JIAZHONG: GongcheMelodySymbol.GAO_WU
        }[lvlv]

    @classmethod
    def to_name(cls, lvlv):
        return {
            cls.HUANGZHONG: "黃",
            cls.DALV: "大",
            cls.TAICU: "太",
            cls.JIAZHONG: "夹",
            cls.GUXIAN: "姑",
            cls.ZHONGLV: "仲",
            cls.RUIBIN: "蕤",
            cls.LINZHONG: "林",
            cls.YIZE: "夷",
            cls.NANLV: "南",
            cls.WUYI: "無",
            cls.YINGZHONG: "應",
            cls.QING_HUANGZHONG: "清黃",
            cls.QING_DALV: "清大",
            cls.QING_TAICU:"清太",
            cls.QING_JIAZHONG: "清夹",
        }[lvlv]

    @classmethod
    def from_name(cls, lvlv):
        return {
            "黃": cls.HUANGZHONG,
            "大": cls.DALV,
            "太": cls.TAICU,
            "夹": cls.JIAZHONG,
            "姑": cls.GUXIAN,
            "仲": cls.ZHONGLV,
            "蕤": cls.RUIBIN,
            "林": cls.LINZHONG,
            "夷": cls.YIZE,
            "南": cls.NANLV,
            "無": cls.WUYI,
            "應": cls.YINGZHONG,
            "清黃": cls.QING_HUANGZHONG,
            "清大": cls.QING_DALV,
            "清太": cls.QING_TAICU,
            "清夹": cls.QING_JIAZHONG,
        }[lvlv]


class NotationAnnotationFrame:
    def __init__(self, window_handle, program_state: ProgramState):
        self.lvlv_list = [ExtendedLvlv.to_name(lvlv) for lvlv in dataclasses.astuple(ExtendedLvlv())]

        self.window_handle = window_handle
        self.program_state = program_state
        self.frame = tk.Frame(self.window_handle)
        self.mode_selector = None
        self.symbol_display = None
        self.musical_var = tk.StringVar(self.frame, "None")
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

        def update_annotation(*args):
            def return_none_if_none(string):
                if string == "None":
                    return None
                return string
            try:
                annotation = {"pitch": return_none_if_none(ExtendedLvlv.from_name(self.musical_var.get()))}
            except Exception:
                annotation = EMPTY_ANNOTATION
            print("SET ANNOTATION", annotation)
            self.program_state.set_current_annotation(annotation)

        def construct_lvlvpu_frame(frame, primary=True):
            prefix = "Pitch" if primary else "Secondary"
            symbol_frame = tk.LabelFrame(frame, text=f"{prefix} Symbol")

            none_button = tk.Radiobutton(symbol_frame,
                                         variable=self.musical_var,
                                         text="", font="Arial 13",
                                         width=4,
                                         height=2,
                                         value="", indicator=0, command=update_annotation)
            none_button.grid(row=0, column=0)
            self._widgets.append(none_button)

            for idx, melody_var in enumerate(self.lvlv_list[0:12]):
                current_button = tk.Radiobutton(symbol_frame,
                                                variable=self.musical_var,
                                                text=melody_var, font="Arial 13",
                                                width=4,
                                                height=2,
                                                value=melody_var, indicator=0, command=update_annotation)
                current_button.grid(row=1, column=idx)
                self._widgets.append(current_button)
            for idx, melody_var in enumerate(self.lvlv_list[12:]):
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

        for widget in self._widgets:
            widget.config(state=state)
        self.mode_selector.set_state(boolean)

    def set_mode_properties(self, props: dict):
        self.mode_selector.set_properties(props)

    def get_mode_properties(self):
        return self.mode_selector.get_properties()