import copy
import dataclasses

from src.suzipu import GongcheMelodySymbol


@dataclasses.dataclass
class ModeProperties:
    gong_lvlv: int
    final_note: str


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

    def get_properties(self) -> ModeProperties:
        return ModeProperties(self.gong_lvlv, self.final_note)


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
    def from_properties(cls, mode_properties: ModeProperties):
        gong_lvlv = mode_properties.gong_lvlv
        final_note = mode_properties.final_note

        for mode in dataclasses.astuple(cls()):  # first, check if there is already a name stored for this mode
            if mode.gong_lvlv == gong_lvlv and mode.final_note == final_note:
                return mode

        # otherwise, construct a name for it
        return GongdiaoMode(f"{Lvlv.to_string(gong_lvlv)}均 -- final：{final_note}", f"{Lvlv.to_string(gong_lvlv)}均 -- final：{final_note}", gong_lvlv, final_note)
