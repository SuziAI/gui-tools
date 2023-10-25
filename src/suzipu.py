import dataclasses

from src.config import SUZIPU_IMAGE_PATH


@dataclasses.dataclass
class NotationType:
    SUZIPU: str = "Suzipu"
    LVLVPU: str = "Lvlvpu"
    GONGCHEPU: str = "Gongchepu"


class SuzipuProperties:
    def __init__(self, name, chinese_name, button_image_filename, basic_pitch=None):
        self.name = name
        self.chinese_name = chinese_name
        self.button_image_filename = f"{SUZIPU_IMAGE_PATH}/{button_image_filename}"
        self.basic_pitch = basic_pitch


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
