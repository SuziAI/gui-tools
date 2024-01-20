import dataclasses
import tkinter as tk

import chinese_converter

from src.auxiliary import open_file_as_tk_image
from src.config import JIANPU_BUTTON_IMAGE, FIVELINE_BUTTON_IMAGE, SUZIPU_IMAGE_PATH
from src.fingering import Fingering


@dataclasses.dataclass
class GongcheMelodySymbol:
    HE: str = "0"
    XIA_SI: str = "1"
    SI: str = "2"
    XIA_YI: str = "3"
    YI: str = "4"
    SHANG: str = "5"
    GOU: str = "6"
    CHE: str = "7"
    XIA_GONG: str = "8"
    GONG: str = "9"
    XIA_FAN: str = "A"
    FAN: str = "B"
    LIU: str = "C"
    XIA_WU: str = "D"
    WU: str = "E"
    GAO_WU: str = "F"

    @classmethod
    def to_lvlv(cls, symbol):
        try:
            return {
                "0": "黃",
                "1": "大",
                "2": "太",
                "3": "夾",
                "4": "姑",
                "5": "仲",
                "6": "蕤",
                "7": "林",
                "8": "夷",
                "9": "南",
                "A": "無",
                "B": "應",
                "C": "清黃",
                "D": "清大",
                "E": "清太",
                "F": "清夾",
            }[symbol]
        except KeyError:
            return "INVALID"

    @classmethod
    def to_gongche(cls, symbol):
        try:
            return {
                "0": "合",
                "1": "下四",
                "2": "四",
                "3": "下一",
                "4": "一",
                "5": "上",
                "6": "勾",
                "7": "尺",
                "8": "下工",
                "9": "工",
                "A": "下凡",
                "B": "凡",
                "C": "六",
                "D": "下五",
                "E": "五",
                "F": "高五",
            }[symbol]
        except KeyError:
            return "INVALID"

    @classmethod
    def to_index(cls, symbol):
        try:
            return {
                "0": 0,
                "1": 1,
                "2": 2,
                "3": 3,
                "4": 4,
                "5": 5,
                "6": 6,
                "7": 7,
                "8": 8,
                "9": 9,
                "A": 10,
                "B": 11,
                "C": 12,
                "D": 13,
                "E": 14,
                "F": 15,
            }[symbol]
        except KeyError:
            return "INVALID"

    @classmethod
    def from_string(cls, str):
        try:
            return {
                "合": "0",
                "下四": "1",
                "四": "2",
                "下一": "3",
                "一": "4",
                "上": "5",
                "勾": "6",
                "尺": "7",
                "下工": "8",
                "工": "9",
                "下凡": "A",
                "凡": "B",
                "六": "C",
                "下五": "D",
                "五": "E",
                "高五": "F",

                "黃": "0",
                "大": "1",
                "太": "2",
                "夾": "3",
                "姑": "4",
                "仲": "5",
                "蕤": "6",
                "林": "7",
                "夷": "8",
                "南": "9",
                "無": "A",
                "應": "B",
                "清黃": "C",
                "清大": "D",
                "清太": "E",
                "清夾": "F",
            }[str]
        except KeyError:
            print(f"'{str}' is not a valid gongche string identifier.")
            return "INVALID"


class Symbol:
    NONE: str = "None"
    ERROR: str = "Error"


@dataclasses.dataclass
class GongdiaoStep:
    GONG: str = "宫"
    SHANG: str = "商"
    JUE: str = "角"
    BIAN: str = "变"
    ZHI: str = "徵"
    YU: str = "羽"
    RUN: str = "闰"


@dataclasses.dataclass
class Lvlv:
    HUANG_ZHONG: int = 0
    DA_LV: int = 1
    TAI_CU: int = 2
    JIA_ZHONG: int = 3
    GU_XIAN: int = 4
    ZHONG_LV: int = 5
    RUI_BIN: int = 6
    LIN_ZHONG: int = 7
    YI_ZE: int = 8
    NAN_LV: int = 9
    WU_YI: int = 10
    YING_ZHONG: int = 11

    @classmethod
    def to_string(cls, lvlv):
        try:
            return {
                cls.HUANG_ZHONG: "黄钟",
                cls.DA_LV: "大吕",
                cls.TAI_CU: "太簇",
                cls.JIA_ZHONG: "夹钟",
                cls.GU_XIAN: "姑洗",
                cls.ZHONG_LV: "仲吕",
                cls.RUI_BIN: "蕤宾",
                cls.LIN_ZHONG: "林钟",
                cls.YI_ZE: "夷则",
                cls.NAN_LV: "南吕",
                cls.WU_YI: "无射",
                cls.YING_ZHONG: "应钟"
            }[lvlv]
        except KeyError:
            print(f"'{lvlv}' is not a valid lülü index, it must be between 0 and 11.")
            return "INVALID"

    @classmethod
    def from_string(cls, string):
        try:
            return {
                "黄钟": cls.HUANG_ZHONG,
                "大吕": cls.DA_LV,
                "太簇": cls.TAI_CU,
                "夹钟": cls.JIA_ZHONG,
                "姑洗": cls.GU_XIAN,
                "仲吕": cls.ZHONG_LV,
                "蕤宾": cls.RUI_BIN,
                "林钟": cls.LIN_ZHONG,
                "夷则": cls.YI_ZE,
                "南吕": cls.NAN_LV,
                "无射": cls.WU_YI,
                "应钟": cls.YING_ZHONG,
            }[string]
        except KeyError:
            print(f"'{string}' is not a valid lülü string")
            return cls.HUANG_ZHONG


def get_tone_inventory(lvlv_idx):
    def rotate_list_right(l, idx):
        return [l[(index - idx + len(l)) % len(l)] for index in range(len(l))]

    def extend_tone_inventory(l):
        return l + l[0:4]

    huang_zhong_gong = ["宫", None, "商", None, "角", None, "变", "徵", None, "羽", None, "闰"]
    return extend_tone_inventory(rotate_list_right(huang_zhong_gong, lvlv_idx))


def tone_inventory_convert_pitch(gong_lvlv, pitch: GongcheMelodySymbol):
    tone_inventory = get_tone_inventory(gong_lvlv)
    def raise_error():
        print(f"Error! Incompatible symbol {pitch} according to tone inventory {tone_inventory}.")
        #raise RuntimeError(f"Error! Incompatible symbol {pitch} according to tone inventory {gong_lvlv}.")

    # Here, we flip the order, because for Nanlüdiao we need the diatonic steps
    if pitch == GongcheMelodySymbol.HE:
        #if gong_lvlv[0] is not None:
        return pitch
    elif pitch == GongcheMelodySymbol.XIA_SI or pitch == GongcheMelodySymbol.SI:
        if tone_inventory[2] is not None:
            return GongcheMelodySymbol.SI
        elif tone_inventory[1] is not None:
            return GongcheMelodySymbol.XIA_SI
    elif pitch == GongcheMelodySymbol.XIA_YI or pitch == GongcheMelodySymbol.YI:
        if tone_inventory[4] is not None:
            return GongcheMelodySymbol.YI
        elif tone_inventory[3] is not None:
            return GongcheMelodySymbol.XIA_YI
    elif pitch == GongcheMelodySymbol.SHANG:
        #if gong_lvlv[5] is not None:
        return pitch
    elif pitch == GongcheMelodySymbol.GOU:  # TODO: Check if GOU, having a separate Suzipu symbol, can become CHE
        #if gong_lvlv[6] is not None:
        return pitch
    elif pitch == GongcheMelodySymbol.CHE:
        #if gong_lvlv[7] is not None:
        return pitch
    elif pitch == GongcheMelodySymbol.XIA_GONG or pitch == GongcheMelodySymbol.GONG:
        if tone_inventory[9] is not None:
            return GongcheMelodySymbol.GONG
        elif tone_inventory[8] is not None:
            return GongcheMelodySymbol.XIA_GONG
    elif pitch == GongcheMelodySymbol.XIA_FAN or pitch == GongcheMelodySymbol.FAN:
        if tone_inventory[11] is not None:
            return GongcheMelodySymbol.FAN
        elif tone_inventory[10] is not None:
            return GongcheMelodySymbol.XIA_FAN
    elif pitch == GongcheMelodySymbol.LIU:
        #if gong_lvlv[12] is not None:
        return pitch
    elif pitch == GongcheMelodySymbol.XIA_WU or pitch == GongcheMelodySymbol.WU:
        if tone_inventory[14] is not None:
            return GongcheMelodySymbol.WU
        elif tone_inventory[13] is not None:
            return GongcheMelodySymbol.XIA_WU
    elif pitch == GongcheMelodySymbol.GAO_WU:
        #if gong_lvlv[15] is not None:
        return pitch

    raise_error()


def tone_inventory_check_pitch(gong_lvlv, pitch: GongcheMelodySymbol):
    tone_inventory = get_tone_inventory(gong_lvlv)

    for idx, cmp_pitch in enumerate(dataclasses.astuple(GongcheMelodySymbol())):
        if pitch == cmp_pitch and tone_inventory[idx] is not None:
            return True
    return False


class GongdiaoMode:
    def __init__(self, name, chinese_name, tone_inventory: int, final_note: str):
        self.name = name
        self.chinese_name = chinese_name
        self.gong_lvlv = tone_inventory
        self.final_note = final_note

    def check_if_pitch_belongs_to_mode(self, pitch: str, is_suzipu: bool=False):

        if pitch == "" or pitch is None:
            return None
        try:
            pitch_symbol = pitch[0]  # only consider first character
            if is_suzipu:  # in case of suzipu, we must convert it to the pitch which is meant first
                pitch_symbol = self.convert_pitch(pitch_symbol)
            return tone_inventory_check_pitch(self.gong_lvlv, pitch_symbol)
        except:
            return None

    def convert_pitch(self, pitch):
        return tone_inventory_convert_pitch(self.gong_lvlv, pitch)

    def convert_pitches_in_list(self, original_list):
        new_list = []
        for idx in range(len(original_list)):
            new_char = ""
            for char in original_list[idx]:
                if char in dataclasses.astuple(GongcheMelodySymbol()):
                    new_char += self.convert_pitch(char)
                else:
                    new_char += char
            new_list.append(new_char)
        return new_list

    def get_properties(self):
        return {"gong_lvlv": self.gong_lvlv, "final_note": self.final_note}


@dataclasses.dataclass
class GongdiaoModeList:
    BAN_SHE_DIAO: GongdiaoMode = GongdiaoMode("Ban She Diao", "般涉调", Lvlv.HUANG_ZHONG, GongdiaoStep.YU)
    DA_SHI_JUE: GongdiaoMode = GongdiaoMode("Da Shi Jue", "大食角", Lvlv.HUANG_ZHONG, GongdiaoStep.RUN)
    ZHENG_GONG : GongdiaoMode= GongdiaoMode("Zheng Gong", "正宫", Lvlv.HUANG_ZHONG, GongdiaoStep.GONG)
    DA_SHI_DIAO: GongdiaoMode = GongdiaoMode("Da Shi Diao", "大食调", Lvlv.HUANG_ZHONG, GongdiaoStep.SHANG)

    HUANG_ZHONG_JUE: GongdiaoMode = GongdiaoMode("*Huang Zhong Jue", "黄钟角", Lvlv.HUANG_ZHONG, GongdiaoStep.JUE)
    HUANG_ZHONG_ZHI: GongdiaoMode = GongdiaoMode("*Huang Zhong Zhi", "黄钟徵", Lvlv.HUANG_ZHONG, GongdiaoStep.ZHI)

    GAO_BAN_SHE_DIAO: GongdiaoMode = GongdiaoMode("Gao Ban She Diao", "高般涉调", Lvlv.DA_LV, GongdiaoStep.YU)
    GAO_DA_SHI_JUE: GongdiaoMode = GongdiaoMode("Gao Da Shi Jue", "高大食角", Lvlv.DA_LV, GongdiaoStep.RUN)
    GAO_GONG: GongdiaoMode = GongdiaoMode("Gao Gong", "高宫", Lvlv.DA_LV, GongdiaoStep.GONG)
    GAO_DA_SHI_DIAO: GongdiaoMode = GongdiaoMode("Gao Da Shi Diao", "高大食调", Lvlv.DA_LV, GongdiaoStep.SHANG)

    ZHONG_LV_DIAO: GongdiaoMode = GongdiaoMode("Zhong Lü Diao", "中吕调", Lvlv.JIA_ZHONG, GongdiaoStep.YU)
    SHUANG_JUE: GongdiaoMode = GongdiaoMode("Shuang Jue", "双角", Lvlv.JIA_ZHONG, GongdiaoStep.RUN)
    ZHONG_LV_GONG: GongdiaoMode = GongdiaoMode("Zhong Lü Gong", "中吕宫", Lvlv.JIA_ZHONG, GongdiaoStep.GONG)
    SHUANG_DIAO: GongdiaoMode = GongdiaoMode("Shuang Diao", "双调", Lvlv.JIA_ZHONG, GongdiaoStep.SHANG)

    ZHENG_PING_DIAO: GongdiaoMode = GongdiaoMode("Zheng Ping Diao", "正平调", Lvlv.ZHONG_LV, GongdiaoStep.YU)
    XIAO_SHI_JUE: GongdiaoMode = GongdiaoMode("Xiao Shi Jue", "小食角", Lvlv.ZHONG_LV, GongdiaoStep.RUN)
    DAO_GONG: GongdiaoMode = GongdiaoMode("Dao Gong", "道宫", Lvlv.ZHONG_LV, GongdiaoStep.GONG)
    XIAO_SHI_DIAO: GongdiaoMode = GongdiaoMode("Xiao Shi Diao", "小食调", Lvlv.ZHONG_LV, GongdiaoStep.SHANG)

    NAN_LV_DIAO: GongdiaoMode = GongdiaoMode("Nan Lü Diao", "南吕调", Lvlv.LIN_ZHONG, GongdiaoStep.YU)  # also 高平调
    XIE_ZHI_JUE: GongdiaoMode = GongdiaoMode("Xie Zhi Jue", "歇指角", Lvlv.LIN_ZHONG, GongdiaoStep.RUN)
    NAN_LV_GONG: GongdiaoMode = GongdiaoMode("Nan Lü Gong", "南吕宫", Lvlv.LIN_ZHONG, GongdiaoStep.GONG)
    XIE_ZHI_DIAO: GongdiaoMode = GongdiaoMode("Xie Zhi Diao", "歇指调", Lvlv.LIN_ZHONG, GongdiaoStep.SHANG)

    XIAN_LV_DIAO: GongdiaoMode = GongdiaoMode("Xian Lü Diao", "仙吕调", Lvlv.YI_ZE, GongdiaoStep.YU)
    SHANG_JUE: GongdiaoMode = GongdiaoMode("Shang Jue", "商角", Lvlv.YI_ZE, GongdiaoStep.RUN)
    XIAN_LV_GONG: GongdiaoMode = GongdiaoMode("Xian Lü Gong", "仙吕宫", Lvlv.YI_ZE, GongdiaoStep.GONG)
    SHANG_DIAO: GongdiaoMode = GongdiaoMode("Shang Diao", "商调", Lvlv.YI_ZE, GongdiaoStep.SHANG)

    HUANG_ZHONG_DIAO: GongdiaoMode = GongdiaoMode("Huang Zhong Diao", "黄钟调", Lvlv.WU_YI, GongdiaoStep.YU)
    YUE_JUE: GongdiaoMode = GongdiaoMode("Yue Jue", "越角", Lvlv.WU_YI, GongdiaoStep.RUN)
    HUANG_ZHONG_GONG: GongdiaoMode = GongdiaoMode("Huang Zhong Gong", "黄钟宫", Lvlv.WU_YI, GongdiaoStep.GONG)
    YUE_DIAO: GongdiaoMode = GongdiaoMode("Yue Diao", "越调", Lvlv.WU_YI, GongdiaoStep.SHANG)

    @classmethod
    def from_string(cls, string):
        for mode in dataclasses.astuple(cls()):
            if string == mode.name or string == mode.chinese_name:
                return mode
        NO_MODE = GongdiaoMode("!!! NO MODE !!!", "！！！没有宫调！！！", Lvlv.HUANG_ZHONG, GongdiaoStep.GONG)
        #print(f"Could not construct mode from string '{string}'. Returned {cls.NO_MODE.name} instead.")  # TODO: activate?
        return NO_MODE

    @classmethod
    def from_properties(cls, mode_properties):
        gong_lvlv = mode_properties["gong_lvlv"]
        final_note = mode_properties["final_note"]

        for mode in dataclasses.astuple(cls()):  # first, check if there is already a name stored for this mode
            if mode.gong_lvlv == gong_lvlv and mode.final_note == final_note:
                return mode

        # otherwise, construct a name for it
        return GongdiaoMode(f"{Lvlv.to_string(gong_lvlv)}均 -- final：{final_note}", f"{Lvlv.to_string(gong_lvlv)}均 -- final：{final_note}", gong_lvlv, final_note)


class DisplayNotesFrame:
    def __init__(self, window_handle, on_save_notation=lambda: None, on_save_musicxml=lambda: None):
        self.window_handle = window_handle
        self.on_save_notation = on_save_notation
        self.on_save_musicxml = on_save_musicxml
        self.frame = tk.LabelFrame(self.window_handle, text="Modern Notation")
        self._image = None
        self.label = tk.Label(self.frame, image=None, relief="sunken", state="disabled")
        self.var_is_jianpu = tk.BooleanVar()
        self.var_is_jianpu.set(True)

        self.transposition_string = tk.StringVar()
        self.transposition_string.set(Fingering.ALL_CLOSED_AS_1.name)

        self.widgets = [self.label]

        self.jianpu_image = open_file_as_tk_image(JIANPU_BUTTON_IMAGE)
        self.fiveline_image = open_file_as_tk_image(FIVELINE_BUTTON_IMAGE)

        self._create_frame()

    def _create_frame(self):
        fingering_names = [fingering.name for fingering in dataclasses.astuple(Fingering())]

        selection_frame = tk.Frame(self.frame)
        jianpu_button = tk.Radiobutton(selection_frame, image=self.jianpu_image, variable=self.var_is_jianpu,
                       value=True,
                       indicator=0, state="disabled")
        fiveline_button = tk.Radiobutton(selection_frame, image=self.fiveline_image, variable=self.var_is_jianpu,
                       value=False,
                       indicator=0, state="disabled")
        transposition_menu = tk.OptionMenu(selection_frame, self.transposition_string, *fingering_names)
        save_notation_to_file_button = tk.Button(selection_frame, text="Export Notation as Image", command=self.on_save_notation)
        save_notation_to_musicxml_button = tk.Button(selection_frame, text="Export Notation as MusicXML",
                                                 command=self.on_save_musicxml)

        jianpu_button.grid(row=0, column=0)
        fiveline_button.grid(row=0, column=1)
        transposition_menu.grid(row=0, column=2)
        save_notation_to_file_button.grid(row=0, column=4)
        save_notation_to_musicxml_button.grid(row=0, column=5)

        self.widgets += [jianpu_button, fiveline_button, transposition_menu, save_notation_to_file_button, save_notation_to_musicxml_button]

        selection_frame.pack()
        self.label.pack(padx=10, pady=10)

    def set_state(self, boolean):
        state = "disabled"
        if boolean:
            state = "normal"

        for widget in self.widgets:
            widget.config(state=state)

    def set_image(self, image):
        self._image = image
        self.label.config(image=self._image)

    def get_frame(self):
        return self.frame

    def is_jianpu(self):
        return self.var_is_jianpu.get()

    def get_transposition(self):
        return Fingering.from_string(self.transposition_string.get())


class StatisticsFrame:
    def __init__(self, window_handle):
        self.window_handle = window_handle
        self.frame = tk.LabelFrame(self.window_handle, text="Statistics")
        self.label = tk.Label(self.frame, image=None, relief="sunken", state="disabled")

        self.button_img_dictionary, self.statistics_text_var_dictionary = self._create_dicts()

        self.widgets = [self.label]

        self._create_frame()

    @classmethod
    def _create_dicts(cls):
        button_img_dictionary = {}
        statistics_text_var_dictionary = {}
        for melody_var in dataclasses.astuple(SuzipuMelodySymbol()):
            button_img_dictionary[melody_var] = open_file_as_tk_image(suzipu_to_info(melody_var).button_image_filename)
            statistics_text_var_dictionary[melody_var] = tk.StringVar()
        for additional_var in dataclasses.astuple(SuzipuAdditionalSymbol()):
            button_img_dictionary[additional_var] = open_file_as_tk_image(suzipu_to_info(additional_var).button_image_filename)
            statistics_text_var_dictionary[additional_var] = tk.StringVar()

        button_img_dictionary[Symbol.NONE] = open_file_as_tk_image(suzipu_to_info(Symbol.NONE).button_image_filename)

        return button_img_dictionary, statistics_text_var_dictionary

    def _create_frame(self):
        selection_frame = tk.Frame(self.frame)

        for idx, melody_var in enumerate(dataclasses.astuple(SuzipuMelodySymbol())):
            current_image = tk.Label(selection_frame, image=self.button_img_dictionary[melody_var], state="disabled", relief="sunken")
            current_text = tk.Label(selection_frame, textvariable=self.statistics_text_var_dictionary[melody_var], state="disabled", relief="sunken", width=3)
            self.widgets += [current_text, current_image]
            current_image.grid(row=0, column=idx, padx=5, pady=5)
            current_text.grid(row=1, column=idx, padx=5, pady=5)
        for idx, additional_var in enumerate(dataclasses.astuple(SuzipuAdditionalSymbol())):
            current_image = tk.Label(selection_frame, image=self.button_img_dictionary[additional_var], state="disabled", relief="sunken")
            current_text = tk.Label(selection_frame, textvariable=self.statistics_text_var_dictionary[additional_var], state="disabled", relief="sunken", width=3)
            self.widgets += [current_text, current_image]
            current_image.grid(row=2, column=idx, padx=5, pady=5)
            current_text.grid(row=3, column=idx, padx=5, pady=5)

        selection_frame.pack()

    def set_state(self, boolean):
        state = "disabled"
        if boolean:
            state = "normal"

        for widget in self.widgets:
            widget.config(state=state)

    def set_statistics(self, dictionary):
        for key in self.statistics_text_var_dictionary:
            self.statistics_text_var_dictionary[key].set("0")
        for key in dictionary:
            self.statistics_text_var_dictionary[key].set(dictionary[key])

    def get_frame(self):
        return self.frame


class NoteFrames:
    def __init__(self, parent_frame):
        self.frame = tk.Frame(parent_frame)
        self.widgets = []
        self.scale_degree_vars_list = []
        self.scale_degree_label_list = []
        self.suzipu_images_list = []
        self._suzipu_images = _create_suzipu_images()
        self._default_bg_color = None

    def get_frame(self):
        lvlv_list = ["黄", "大", "太", "夹", "姑", "仲", "蕤", "林", "夷", "南", "无", "应", "黄清", "大清", "太清",
                     "夹清"]
        gongche_list = ["合", "下四", "四", "下一", "一", "上", "勾", "尺", "下工", "工", "下凡", "凡", "六",
                        "下五", "五", "高五"]

        labels_frame = tk.Frame(self.frame)
        lvlv_label = tk.Label(labels_frame, text="律吕")
        gongche_label = tk.Label(labels_frame, text="工尺")
        scale_degree_label = tk.Label(labels_frame, text="声音阶")
        suzipu_label = tk.Label(labels_frame, text="俗字谱")

        lvlv_label.grid(row=0, column=0, padx=10, pady=5)
        gongche_label.grid(row=1, column=0, padx=10, pady=5)
        scale_degree_label.grid(row=2, column=0, padx=10, pady=5)
        suzipu_label.grid(row=3, column=0, padx=10, pady=5)

        labels_frame.grid(row=0, column=0)

        for idx in range(len(lvlv_list)):
            subframe = tk.LabelFrame(self.frame)
            textvar = tk.StringVar()
            self.scale_degree_vars_list.append(textvar)

            lvlv_label = tk.Label(subframe, text=lvlv_list[idx])
            gongche_label = tk.Label(subframe, text=gongche_list[idx])
            scale_degree_label = tk.Label(subframe, textvariable=textvar, relief="sunken", width=3)
            suzipu_label = tk.Label(subframe, image=self._suzipu_images[Symbol.NONE], relief="sunken")
            self.suzipu_images_list.append(suzipu_label)
            self.scale_degree_label_list.append(scale_degree_label)

            lvlv_label.grid(row=0, column=0, padx=10, pady=5)
            gongche_label.grid(row=1, column=0, padx=10, pady=5)
            scale_degree_label.grid(row=2, column=0, padx=10, pady=5)
            suzipu_label.grid(row=3, column=0, padx=10, pady=5)

            subframe.grid(row=0, column=idx+1)
            self.widgets += [lvlv_label, gongche_label, scale_degree_label, suzipu_label]

        self._default_bg_color = suzipu_label.cget("bg")
        return self.frame

    def update(self, mode: GongdiaoMode):
        final_note = mode.final_note
        tone_inventory = get_tone_inventory(mode.gong_lvlv)

        for idx in range(len(self.scale_degree_vars_list)):
            scale_degree = tone_inventory[idx] if tone_inventory[idx] else ""
            gongche_melody_symbol = dataclasses.astuple(GongcheMelodySymbol())[idx]

            pitch = gongche_melody_symbol if gongche_melody_symbol == mode.convert_pitch(gongche_melody_symbol) else None

            self.scale_degree_vars_list[idx].set(scale_degree)
            self.suzipu_images_list[idx].config(image=self._suzipu_images[pitch])

            self.scale_degree_label_list[idx].config(bg="aquamarine" if scale_degree == final_note else self._default_bg_color)

    def set_state(self, boolean):
        state = "disabled"
        if boolean:
            state = "normal"
        for widget in self.widgets:
            widget.config(state=state)


class ModeSelectorFrame:
    def __init__(self, window_handle, mode_variable, on_get_mode_string=lambda: None):
        self.window_handle = window_handle
        self.frame = tk.LabelFrame(self.window_handle, text="Mode")

        self.mode_variable = mode_variable
        self.mode_gong_lvlv = tk.IntVar()
        self.mode_final_note = tk.StringVar()
        self.mode_final_note.set("宫")

        self.widgets = None
        self.get_mode_string = on_get_mode_string

        self._create_frame()

    def get_properties(self):
        return {"gong_lvlv": self.mode_gong_lvlv.get(), "final_note": self.mode_final_note.get()}

    def set_properties(self, mode_properties):
        self.mode_gong_lvlv.set(mode_properties["gong_lvlv"])
        self.mode_final_note.set(mode_properties["final_note"])

    def _create_frame(self):
        def on_update_mode_properties(*args, **kwargs):
            mode = GongdiaoModeList.from_string(self.mode_variable.get())
            self.mode_final_note.set(mode.final_note)
            self.mode_gong_lvlv.set(mode.gong_lvlv)

        def on_infer_mode():
            mode_string = self.get_mode_string()
            mode = GongdiaoModeList.from_string(chinese_converter.to_simplified(mode_string))
            self.mode_variable.set(mode.name)
            self.mode_gong_lvlv.set(mode.gong_lvlv)
            self.mode_final_note.set(mode.final_note)

        def on_custom_mode():
            def execute_custom_mode_window():
                custom_mode_window = tk.Toplevel()
                gong_lvlv_var = tk.StringVar()
                gong_lvlv_var.set(Lvlv.to_string(Lvlv.HUANG_ZHONG))
                final_note_var = tk.StringVar()
                final_note_var.set(GongdiaoStep.GONG)
                exit_save_var = tk.BooleanVar()
                exit_save_var.set(False)

                def on_destroy_save_changes():
                    exit_save_var.set(True)
                    custom_mode_window.destroy()

                lvlv_list = [Lvlv.to_string(lvlv) for lvlv in dataclasses.astuple(Lvlv())]
                final_note_list = dataclasses.astuple(GongdiaoStep())

                selection_frame = tk.Frame(custom_mode_window)
                lvlv_label = tk.Label(selection_frame, text="Mode's 宫")
                lvlv_selector = tk.OptionMenu(selection_frame, gong_lvlv_var, gong_lvlv_var.get(), *lvlv_list)
                final_note_label = tk.Label(selection_frame, text="Mode's Final Note")
                final_note_selector = tk.OptionMenu(selection_frame, final_note_var, final_note_var.get(), *final_note_list)

                lvlv_label.grid(row=0, column=0)
                lvlv_selector.grid(row=0, column=1)
                final_note_label.grid(row=1, column=0)
                final_note_selector.grid(row=1, column=1)

                ok_button = tk.Button(custom_mode_window, text="OK", command=on_destroy_save_changes)
                selection_frame.grid(row=0, column=0)
                ok_button.grid(row=1, column=0)

                custom_mode_window.wait_window()

                return exit_save_var.get(), gong_lvlv_var.get(), final_note_var.get()

            exit_save_var, gong_lvlv_string, final_note = execute_custom_mode_window()

            if exit_save_var:
                gong_lvlv = Lvlv.from_string(gong_lvlv_string)

                mode = GongdiaoModeList.from_properties({"gong_lvlv": gong_lvlv, "final_note": final_note})
                self.mode_variable.set(mode.name)
                self.mode_gong_lvlv.set(mode.gong_lvlv)
                self.mode_final_note.set(mode.final_note)

        sub_frame = tk.Frame(self.frame)
        mode_names = [mode.name for mode in dataclasses.astuple(GongdiaoModeList())]
        mode_menu = tk.OptionMenu(sub_frame, self.mode_variable, "", *mode_names, command=on_update_mode_properties)
        infer_mode_button = tk.Button(sub_frame, text="Infer Mode from Segmentation Boxes", command=on_infer_mode)
        custom_mode_button = tk.Button(sub_frame, text="Custom Mode Picker", command=on_custom_mode)
        mode_menu.grid(row=0, column=0)
        infer_mode_button.grid(row=0, column=1)
        custom_mode_button.grid(row=0, column=2)
        sub_frame.pack()

        self.widgets = [mode_menu, infer_mode_button, custom_mode_button]

    def set_state(self, boolean):
        state = "disabled"
        if boolean:
            state = "normal"
        for widget in self.widgets:
            widget.config(state=state)

    def get_frame(self):
        return self.frame


class ModeDisplayFrame:
    def __init__(self, window_handle, mode_variable, on_get_mode_string=lambda: None):
        self.window_handle = window_handle
        self.frame = tk.LabelFrame(self.window_handle, text="Mode")

        self.mode_variable = mode_variable
        self.mode_gong_lvlv = tk.IntVar()
        self.mode_final_note = tk.StringVar()
        self.mode_final_note.set("宫")

        self.widgets = None
        self.get_mode_string = on_get_mode_string

        self.note_frames = NoteFrames(self.frame)

        self._create_frame()

    def get_properties(self):
        return {"gong_lvlv": self.mode_gong_lvlv.get(), "final_note": self.mode_final_note.get()}

    def set_properties(self, mode_properties):
        self.mode_gong_lvlv.set(mode_properties["gong_lvlv"])
        self.mode_final_note.set(mode_properties["final_note"])

    def _create_frame(self):
        zhuyin_label = tk.Label(self.frame, text="(Final is marked in cyan)")
        self.note_frames.get_frame().grid(row=0, column=0)
        zhuyin_label.grid(row=1, column=0)

    def set_state(self, boolean):
        pass

    def get_frame(self):
        return self.frame


class AdditionalInfoFrame:
    def __init__(self, window_handle, mode_variable, on_save_notation=lambda: None, on_save_musicxml=lambda: None, get_mode_string=lambda: None):
        self.window_handle = window_handle
        self.frame = tk.Frame(self.window_handle)
        self.mode_statistics_frame = tk.Frame(self.frame)

        self.mode_frame = ModeSelectorFrame(self.mode_statistics_frame, mode_variable, get_mode_string)
        self.statistics_frame = StatisticsFrame(self.mode_statistics_frame)
        self.display_frame = DisplayNotesFrame(self.frame, on_save_notation, on_save_musicxml)

        self.mode_frame.get_frame().grid(row=0, column=0, padx=5, pady=5)
        self.statistics_frame.get_frame().grid(row=1, column=0, padx=5, pady=5)

        self.mode_statistics_frame.grid(row=0, column=0, padx=5, pady=5)
        self.display_frame.get_frame().grid(row=0, column=1, padx=5, pady=5)

    def set_state(self, boolean):
        self.statistics_frame.set_state(boolean)
        self.display_frame.set_state(boolean)
        self.mode_frame.set_state(boolean)

    def set_image(self, image):
        self.display_frame.set_image(image)

    def set_statistics(self, dictionary):
        self.statistics_frame.set_statistics(dictionary)

    def get_frame(self):
        return self.frame

    def is_jianpu(self):
        return self.display_frame.is_jianpu()

    def get_transposition(self):
        return self.display_frame.get_transposition()

    def get_mode_properties(self):
        return self.mode_frame.get_properties()

    def set_mode_properties(self, mode_properties):
        return self.mode_frame.set_properties(mode_properties)


class SuzipuProperties:
    def __init__(self, name, chinese_name, button_image_filename, basic_pitch=None):
        self.name = name
        self.chinese_name = chinese_name
        self.button_image_filename = f"{SUZIPU_IMAGE_PATH}/{button_image_filename}"
        self.basic_pitch = basic_pitch


@dataclasses.dataclass()
class SuzipuMelodySymbol:
    HE: str = GongcheMelodySymbol.HE
    SI: str = GongcheMelodySymbol.SI
    YI: str = GongcheMelodySymbol.YI
    SHANG: str = GongcheMelodySymbol.SHANG
    GOU: str = GongcheMelodySymbol.GOU
    CHE: str = GongcheMelodySymbol.CHE
    GONG: str = GongcheMelodySymbol.GONG
    FAN: str = GongcheMelodySymbol.FAN
    LIU: str = GongcheMelodySymbol.LIU
    WU: str = GongcheMelodySymbol.WU
    GAO_WU: str = GongcheMelodySymbol.GAO_WU


@dataclasses.dataclass
class SuzipuAdditionalSymbol:
    ADD_DA_DUN: str = ":"
    ADD_XIAO_ZHU: str = "."
    ADD_DING_ZHU: str = "#"
    ADD_DA_ZHU: str = ";"
    ADD_ZHE: str = "z"
    ADD_YE: str = "y"


def _create_suzipu_images():
    dictionary = {}
    for melody_var in dataclasses.astuple(GongcheMelodySymbol()):
        dictionary[melody_var] = open_file_as_tk_image(suzipu_to_info(melody_var).button_image_filename)
    for additional_var in dataclasses.astuple(SuzipuAdditionalSymbol()):
        dictionary[additional_var] = open_file_as_tk_image(suzipu_to_info(additional_var).button_image_filename)
    dictionary[Symbol.NONE] = open_file_as_tk_image(suzipu_to_info(Symbol.NONE).button_image_filename)
    dictionary[Symbol.ERROR] = open_file_as_tk_image(suzipu_to_info(Symbol.ERROR).button_image_filename)
    dictionary[None] = open_file_as_tk_image(suzipu_to_info(Symbol.NONE).button_image_filename)

    return dictionary


def suzipu_to_info(suzipu_base_symbol) -> SuzipuProperties:
    suzipu_to_info_dict = {
        GongcheMelodySymbol.HE: SuzipuProperties("He", "合", "he.png", "C4"),
        GongcheMelodySymbol.XIA_SI: SuzipuProperties("Xia Si", "下四", "si.png", "Db4"),
        GongcheMelodySymbol.SI: SuzipuProperties("Si", "四", "si.png", "D4"),
        GongcheMelodySymbol.XIA_YI: SuzipuProperties("Xia Yi", "下一", "yi.png", "Eb4"),
        GongcheMelodySymbol.YI: SuzipuProperties("Yi", "一", "yi.png", "E4"),
        GongcheMelodySymbol.SHANG: SuzipuProperties("Shang", "上", "shang.png", "F4"),
        GongcheMelodySymbol.GOU: SuzipuProperties("Gou", "勾", "gou.png", "F#4"),
        GongcheMelodySymbol.CHE: SuzipuProperties("Che", "尺", "che.png", "G4"),
        GongcheMelodySymbol.XIA_GONG: SuzipuProperties("Xia Gong", "下工", "gong.png", "Ab4"),
        GongcheMelodySymbol.GONG: SuzipuProperties("Gong", "工", "gong.png", "A4"),
        GongcheMelodySymbol.XIA_FAN: SuzipuProperties("Xia Fan", "下凡", "fan.png", "Bb4"),
        GongcheMelodySymbol.FAN: SuzipuProperties("Fan", "凡", "fan.png", "B4"),
        GongcheMelodySymbol.LIU: SuzipuProperties("Liu", "六", "liu.png", "C5"),
        GongcheMelodySymbol.XIA_WU: SuzipuProperties("Xia Wu", "下五", "wu.png", "Db5"),
        GongcheMelodySymbol.WU: SuzipuProperties("Wu", "五", "wu.png", "D5"),
        GongcheMelodySymbol.GAO_WU: SuzipuProperties("Gao Wu", "高五", "gao_wu.png", "Eb5"),

        SuzipuAdditionalSymbol.ADD_DA_DUN: SuzipuProperties("ADD_Dadun", "大顿", "add_dadun.png"),
        SuzipuAdditionalSymbol.ADD_XIAO_ZHU: SuzipuProperties("ADD_Xiaozhu", "小住", "add_xiaozhu.png"),
        SuzipuAdditionalSymbol.ADD_DING_ZHU: SuzipuProperties("ADD_Dingzhu", "丁住", "add_dingzhu.png"),
        SuzipuAdditionalSymbol.ADD_DA_ZHU: SuzipuProperties("ADD_Dazhu", "大住", "add_dazhu.png"),
        SuzipuAdditionalSymbol.ADD_ZHE: SuzipuProperties("ADD_Zhe", "折", "add_zhe.png"),
        SuzipuAdditionalSymbol.ADD_YE: SuzipuProperties("ADD_Ye", "拽", "add_ye.png"),

        Symbol.NONE: SuzipuProperties("None", "None", "none.png"),
        Symbol.ERROR: SuzipuProperties("None", "None", "error.png"),
    }

    try:
        return suzipu_to_info_dict[suzipu_base_symbol]
    except KeyError as e:
        print(f"Expected Suzipu base symbol string, but received {suzipu_base_symbol}. {e}")