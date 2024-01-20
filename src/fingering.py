import dataclasses

import music21


class FingeringProperties:
    def __init__(self, name, chinese_name, transposition_index, image_data):
        self.name = name
        self.chinese_name = chinese_name
        self.transposition_index = transposition_index
        self.image_data = image_data


@dataclasses.dataclass
class Fingering:
    ALL_CLOSED_AS_1: FingeringProperties = FingeringProperties(name="Lowest = •1", chinese_name="筒音作 •1", transposition_index="-P8", image_data=("1", "low", None))
    ALL_CLOSED_AS_2: FingeringProperties = FingeringProperties(name="Lowest = •2", chinese_name="筒音作 •2", transposition_index="-m7", image_data=("2", "low", None))
    ALL_CLOSED_AS_3: FingeringProperties = FingeringProperties(name="Lowest = •3", chinese_name="筒音作 •3", transposition_index="-m6", image_data=("3", "low", None))
    ALL_CLOSED_AS_4: FingeringProperties = FingeringProperties(name="Lowest = •4", chinese_name="筒音作 •4", transposition_index="-P5", image_data=("4", "low", None))
    ALL_CLOSED_AS_5: FingeringProperties = FingeringProperties(name="Lowest = •5", chinese_name="筒音作 •5", transposition_index="-P4", image_data=("5", "low", None))
    ALL_CLOSED_AS_6: FingeringProperties = FingeringProperties(name="Lowest = •6", chinese_name="筒音作 •6", transposition_index="-m3", image_data=("6", "low", None))
    ALL_CLOSED_AS_FLAT_7: FingeringProperties = FingeringProperties(name="Lowest = •♭7", chinese_name="筒音作 •♭7", transposition_index="-M2", image_data=("7", "low", "flat"))

    @classmethod
    def from_string(cls, string):
        for fingering in dataclasses.astuple(cls()):
            if string == fingering.name or string == fingering.chinese_name:
                return fingering
        fingering = Fingering.ALL_CLOSED_AS_1
        print(f"Could not detect fingering from name '{string}'. Returned {fingering.name} instead.")
        return fingering


def fingering_to_lowest_note(fingering: FingeringProperties):
    transposition = fingering.transposition_index
    base_note = music21.note.Note("C4")
    base_note = base_note.transpose(transposition)
    return base_note
