import dataclasses

from src.plugins.suzipu_lvlvpu_gongchepu.common import GongcheMelodySymbol


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

    @classmethod
    def from_class(cls, idx):
        return dataclasses.astuple(cls())[idx]

    @classmethod
    def to_class(cls, extended_lvlv):
        try:
            return dataclasses.astuple(cls()).index(extended_lvlv)
        except ValueError:
            return 7  # LINZHONG
