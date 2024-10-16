import dataclasses
import json
import tkinter as tk
import tkinter.ttk
from tkinter.messagebox import askyesno

import PIL
from PIL import ImageTk

from src.auxiliary import BoxType
from src.plugins.suzipu_lvlvpu_gongchepu.notes_to_image import common_notation_to_jianpu, common_notation_to_staff, \
    NotationResources, notation_to_text
from src.plugins.suzipu_lvlvpu_gongchepu.suzipu_intelligent_assistant import load_model, load_transforms, predict_all
from src.programstate import ProgramState
from src.config import CHINESE_FONT_FILE
from src.plugins.suzipu_lvlvpu_gongchepu.common import Symbol, SuzipuMelodySymbol, SuzipuAdditionalSymbol, \
    _create_suzipu_images, ModeSelectorFrame, Lvlv, GongcheMelodySymbol


EMPTY_ANNOTATION = None
PLUGIN_NAME = "No Notation"
DISPLAY_NOTATION = True
HAS_MUSICXML = False


RESOURCES = NotationResources()


def notation_to_own(mode, music_list, lyrics_list, line_break_idxs, fingering, return_boxes=False, is_vertical=False):
    return notation_to_text(
                    RESOURCES.small_font,
                    RESOURCES.smallest_font,
                    lyrics_list,
                    line_break_idxs,
                    return_boxes,
                    is_vertical)


class NotationAnnotationFrame:
    def __init__(self, window_handle, program_state: ProgramState, simple=False):
        self.program_state = program_state
        self.window_handle = window_handle
        self.frame = tk.Frame(self.window_handle)
        self.mode_selector = None
        self.simple = simple

        self._create_frame()


    def update_display(self):
        pass

    def _create_frame(self):
        self.mode_selector = ModeSelectorFrame(self.frame,
                                               mode_variable=self.program_state.gui_state.tk_current_mode_string,
                                               on_get_mode_string=self.program_state.get_mode_string)

        mode_selector_frame = self.mode_selector.get_frame()
        mode_selector_frame.pack()

    def get_frame(self):
        return self.frame

    def set_state(self, boolean):
        pass

    def set_mode_properties(self, props: dict):
        self.mode_selector.set_properties(props)

    def get_mode_properties(self):
        return self.mode_selector.get_properties()