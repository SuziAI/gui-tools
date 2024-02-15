import dataclasses
import os

from PIL import Image, ImageChops, ImageDraw, ImageFont
import music21
import argparse
import json

from src.fingering import FingeringProperties, Fingering, fingering_to_lowest_note
from src.plugins.suzipu_lvlvpu_gongchepu.common import GongcheMelodySymbol, GongdiaoModeList, SuzipuAdditionalSymbol, \
    suzipu_to_info
from src.config import JIANPU_IMAGE_PATH, FIVELINE_IMAGE_PATH, CHINESE_FONT_FILE, SUZIPU_NOTATION_IMAGE_PATH

accidental_dictionary = {
            "None": None,
            "<music21.pitch.Accidental flat>": "flat",
            "<music21.pitch.Accidental natural>": "natural",
            "<music21.pitch.Accidental sharp>": "sharp",
            "<music21.pitch.Accidental double-sharp>": "double_sharp",
            "<music21.pitch.Accidental double-flat>": "double_flat",
        }


additional_symbol_dictionary = {
            None: "add_none",
            SuzipuAdditionalSymbol.ADD_DA_DUN: "add_dadun",
            SuzipuAdditionalSymbol.ADD_XIAO_ZHU: "add_xiaozhu",
            SuzipuAdditionalSymbol.ADD_DING_ZHU: "add_dingzhu",
            SuzipuAdditionalSymbol.ADD_DA_ZHU: "add_dazhu",
            SuzipuAdditionalSymbol.ADD_ZHE: "add_zhe",
            SuzipuAdditionalSymbol.ADD_YE: "add_ye",

        }


def load_jianpu_image_dict():
    image_dict = {}
    for image_path in os.listdir(JIANPU_IMAGE_PATH):
        image_dict[os.path.basename(image_path).split(".")[0]] = Image.open(f"{JIANPU_IMAGE_PATH}/{image_path}").convert("RGB")
    return image_dict


def load_western_image_dict():
    image_dict = {}
    for image_path in os.listdir(FIVELINE_IMAGE_PATH):
        image_dict[os.path.basename(image_path).split(".")[0]] = Image.open(f"{FIVELINE_IMAGE_PATH}/{image_path}").convert("RGB")
    return image_dict


def load_suzipu_image_dict():
    image_dict = {}
    for image_path in os.listdir(SUZIPU_NOTATION_IMAGE_PATH):
        image_dict[os.path.basename(image_path).split(".")[0]] = Image.open(f"{SUZIPU_NOTATION_IMAGE_PATH}/{image_path}").convert("RGB")
    return image_dict


def load_font(font_size):
    from matplotlib import font_manager
    font = font_manager.FontProperties(fname=CHINESE_FONT_FILE)
    file = font_manager.findfont(font)
    font = ImageFont.truetype(file, font_size)
    return font


class NotationResources:
    def __init__(self):
        self.smallest_font = load_font(25)
        self.small_font = load_font(40)
        self.title_font = load_font(70)

        self.jianpu_image_dict = load_jianpu_image_dict()
        self.western_image_dict = load_western_image_dict()
        self.suzipu_image_dict = load_suzipu_image_dict()


def parse_arguments():
    parser = argparse.ArgumentParser(description="WriteSuzipuListToFile")
    parser.add_argument("--music_list", required=True,
                        help="JSON string containing the notational information.")
    parser.add_argument("--lyrics_list", required=True,
                        help="JSON string containing the lyrics information.")
    parser.add_argument("--output_file_path", default="temp.png", required=False,
                        help="Path to the output file.")
    parser.add_argument("--line_break_idxs", default=[], required=False,
                        help="List of the indices after which a line break occurs.")
    parser.add_argument("--title", default="", required=False,
                        help="Piece title.")
    parser.add_argument("--mode", default="", required=False,
                        help="Piece mode.")
    parser.add_argument("--preface", default="", required=False,
                        help="Piece preface.")
    return parser.parse_args()


def horizontal_composition(image_list: list):
    width = sum([image.width for image in image_list])
    height = max([image.height for image in image_list])

    whole_image = Image.new('RGB', (width, height), (255, 255, 255))

    width_offset = 0
    for image in image_list:
        whole_image.paste(image, (width_offset, 0))
        width_offset += image.width

    return whole_image


def vertical_composition(image_list: list):
    height = sum([image.height for image in image_list])
    width = max([image.width for image in image_list])

    whole_image = Image.new('RGB', (width, height), (255, 255, 255))

    height_offset = 0
    for image in image_list:
        whole_image.paste(image, (0, height_offset))
        height_offset += image.height

    return whole_image


def add_border(image, border_width, border_heigth):
    new_image = Image.new('RGB', (image.width + border_width, image.height + border_heigth), (255, 255, 255))
    new_image.paste(image, (border_width//2, border_heigth//2))
    return new_image


def apply_border_to_boxes(boxes, border_width, border_heigth):
    new_boxes = []
    for idx in range(len(boxes)):
        p1_x = boxes[idx][0][0] + border_width
        p1_y = boxes[idx][0][1] + border_heigth
        p2_x = boxes[idx][1][0] + border_width
        p2_y = boxes[idx][1][1] + border_heigth
        new_boxes.append(((p1_x, p1_y), (p2_x, p2_y)))

    return new_boxes


def construct_note_stream(notation_list, lyrics_list, line_break_idxs):
    stream = music21.stream.Stream()

    current_measure = music21.stream.Measure()
    for box_idx, notation in enumerate(notation_list):

        pitch = notation["pitch"]

        try:
            secondary = notation["secondary"]
        except KeyError:
            secondary = None

        if not pitch:
            note = music21.note.Rest()
            note.lyric = lyrics_list[box_idx]

            note.additional_symbol = None
            note.line_break = False
            note.original_pitch = None

            if box_idx in line_break_idxs:
                note.line_break = True

            current_measure.append([note])
        else:
            pitch = suzipu_to_info(pitch).basic_pitch

            note = music21.note.Note(pitch, type="16th")
            note.lyric = lyrics_list[box_idx]

            note.line_break = False
            if box_idx in line_break_idxs:
                note.line_break = True

            note.additional_symbol = secondary
            note.original_pitch = pitch

            current_measure.append([note])
    stream.append(current_measure)

    return stream


def construct_note_stream_musicxml(suzipu_list, lyrics_list):
    stream = music21.stream.Stream()

    current_measure = music21.stream.Measure()
    for box_idx, string in enumerate(suzipu_list):
        print(lyrics_list[box_idx])
        if string["pitch"] is None or string["pitch"] == "None":  # Case 1: no suzipu notation in the box
            note = music21.note.Rest(length="quarter")
            note.lyric = lyrics_list[box_idx]

            if note.lyric == "" or note.lyric is None:  # In case we have no lyric here, do not append, but make the last barline a double bar
                if len(current_measure) == 0:
                    current_measure.leftBarline = music21.bar.Barline(type="double")
                else:  # except when we already have some notes in there, then make a new bar
                    current_measure = music21.stream.Measure()
                    current_measure.leftBarline = music21.bar.Barline(type="double")
                continue
            else:
                current_measure.append([note])
        else:
            char1 = string["pitch"]

            try:
                char2 = string["secondary"]
            except KeyError:
                char2 = None

            pitch1 = suzipu_to_info(char1).basic_pitch if char1 else None
            pitch2 = suzipu_to_info(char2).basic_pitch if char2 else None

            if char1 is None or char2 is None:  # Case 2a: No pair-character notation, i.e., single pitch
                pitch = pitch1 if pitch1 else pitch2
                note = music21.note.Note(pitch, type="quarter")
                note.lyric = lyrics_list[box_idx]
                current_measure.append(note)

            elif pitch1 and pitch2:  # Case 2b: Two pitches in the pair-character notation
                note1 = music21.note.Note(pitch1, type="quarter")
                note1.lyric = lyrics_list[box_idx]
                note2 = music21.note.Note(pitch2, type="quarter")
                current_measure.append([note1, note2])
                current_measure.insert(0.0, music21.spanner.Slur([note1, note2]))
            elif (char1 == SuzipuAdditionalSymbol.ADD_DING_ZHU or char2 == SuzipuAdditionalSymbol.ADD_DING_ZHU or
                  char1 == SuzipuAdditionalSymbol.ADD_ZHE or char2 == SuzipuAdditionalSymbol.ADD_ZHE or
                  char1 == SuzipuAdditionalSymbol.ADD_YE or char2 == SuzipuAdditionalSymbol.ADD_YE):  # Case 2c: additional symbol resulting in multiple notes
                pitch = pitch1 if pitch1 else pitch2
                note1 = music21.note.Note(pitch, type="quarter")
                note1.lyric = lyrics_list[box_idx]

                if char1 == SuzipuAdditionalSymbol.ADD_DING_ZHU or char2 == SuzipuAdditionalSymbol.ADD_DING_ZHU:
                    note2 = music21.note.Note(pitch, type="quarter")
                    current_measure.append([note1, note2])
                    stream.append(current_measure)
                    current_measure = music21.stream.Measure()  # insert barline after this, signifying "slight pause"
                    continue
                elif char1 == SuzipuAdditionalSymbol.ADD_ZHE or char2 == SuzipuAdditionalSymbol.ADD_ZHE:
                    note2 = music21.note.Note(pitch, type="quarter")
                    note2 = note2.transpose("m2")
                else:  # char1 or char2 equal SuzipuAdditionalSymbol.ADD_YE
                    note2 = music21.note.Note(pitch, type="quarter")
                    note2 = note2.transpose("M2")

                current_measure.append([note1, note2])
                current_measure.insert(0.0, music21.spanner.Slur([note1, note2]))
            else:  # Case 2d: additional symbol resulting in prolongation of original pitch
                pitch = pitch1 if pitch1 else pitch2
                if char1 == SuzipuAdditionalSymbol.ADD_DA_DUN or char2 == SuzipuAdditionalSymbol.ADD_DA_DUN:
                    note = music21.note.Note(pitch, quarterLength=3)  # triple the time
                    note.lyric = lyrics_list[box_idx]
                    current_measure.append(note)
                    current_measure.append(music21.note.Rest(length="quarter"))  # add long pause
                elif char1 == SuzipuAdditionalSymbol.ADD_XIAO_ZHU or char2 == SuzipuAdditionalSymbol.ADD_XIAO_ZHU:
                    note = music21.note.Note(pitch, type="half")  # double the time
                    note.lyric = lyrics_list[box_idx]
                    current_measure.append(note)
                else:  # char1 or char2 equal SuzipuAdditionalSymbol.ADD_DA_ZHU
                    note = music21.note.Note(pitch, type="half", dots=1)  # triple the time
                    note.lyric = lyrics_list[box_idx]
                    current_measure.append(note)

                stream.append(current_measure)
                current_measure = music21.stream.Measure()  # insert barline after this, signifying "slight pause"

    if len(current_measure) == 0:  # if last measure contains no notes, apply final bar to previous measure
        stream.getElementsByClass(music21.stream.Measure)[-1].rightBarline = music21.bar.Barline(type="final")
    else:
        current_measure.rightBarline = music21.bar.Barline(type="final")
        stream.append(current_measure)

    # assign each bar its correct time signature to avoid duration errors
    from fractions import Fraction
    for m in stream.recurse().getElementsByClass('Measure'):
        d = Fraction(m.duration.quarterLength / 4.0)
        ts = music21.meter.TimeSignature(str(d.numerator) + '/' + str(d.denominator))
        ts.style.hideObjectOnPrint = True
        m.insert(0, ts)

    return stream


def determine_image_width(stream):
    max_counter = -1

    counter = 0
    for measure in stream:
        for idx, note in enumerate(measure):
            if note.line_break or idx == len(measure)-1:
                max_counter = max(counter+1, max_counter)
                counter = 0
            else:
                counter += 1

    return max_counter


def parse_notation_and_write_to_file(suzipu_list, lyrics_list, output_file_path_str: str):
    stream = music21.stream.Stream()

    measures = []
    current_measure = music21.stream.Measure()
    for box_idx, str in enumerate(suzipu_list):
        char1 = str[0]
        char2 = None
        try:
            char2 = str[1]
        except IndexError:
            pass

        pitch1 = suzipu_to_info(char1).basic_pitch if char1 else None
        pitch2 = suzipu_to_info(char2).basic_pitch if char2 else None

        if pitch1 and pitch2:
            note1 = music21.note.Note(pitch1, type="half")
            note1.lyric = lyrics_list[box_idx]
            note2 = music21.note.Note(pitch2, type="half")
            current_measure.append([note1, note2])
        else:
            pitch = pitch1 if pitch1 else pitch2
            note = music21.note.Note(pitch, type="whole")
            note.lyric = lyrics_list[box_idx]
            current_measure.append([note])

        if char1 == SuzipuAdditionalSymbol.ADD_XIAO_ZHU_1 or char2 == SuzipuAdditionalSymbol.ADD_XIAO_ZHU_1:
            measures.append(current_measure)
            current_measure = music21.stream.Measure()

    measures.append(current_measure)
    stream.append(measures)

    # if os.path.exists(output_file_path):
    #    os.remove(output_file_path)

    stream.write("lily.png", fp=output_file_path_str)


def common_notation_to_jianpu(font, image_dict, mode, music_list, lyrics_list, line_break_idxs=[], fingering=Fingering.ALL_CLOSED_AS_1, return_boxes=False):
    pitch_past = []

    width = 65

    if mode:
        try:
            music_list = mode.convert_pitches_in_list(music_list)
        except TypeError:  # This happens when the chosen mode dows not match the piece
            return None

    def note_to_suzipu(font, note, image_dict):
        pitch_dictionary = {
            "C": "1",
            "D": "2",
            "E": "3",
            "F": "4",
            "G": "5",
            "A": "6",
            "B": "7",
        }

        class OctaveIdentifier:
            DOUBLE_LOW = 2
            LOW = 3
            NORMAL = 4
            HIGH = 5
            DOUBLE_HIGH = 6

        octave_dictionary = {
            OctaveIdentifier.DOUBLE_LOW: "double_low",
            OctaveIdentifier.LOW: "low",
            OctaveIdentifier.NORMAL: None,
            OctaveIdentifier.HIGH: "high",
            OctaveIdentifier.DOUBLE_HIGH: "double_high",
        }

        whole_img = Image.new('RGB', (width, width * 3), (255, 255, 255))
        pitch_img = Image.new('RGB', (width, width), (255, 255, 255))
        lyric = note.lyric

        if note.isRest:
            pass
        else:
            additional_symbol = additional_symbol_dictionary[note.additional_symbol]
            pitch_idx = pitch_dictionary[note.pitch.step]
            octave = octave_dictionary[note.pitch.octave]

            note.pitch.updateAccidentalDisplay(pitchPast=pitch_past)
            pitch_past.append(note.pitch)

            accidental = accidental_dictionary[repr(note.pitch.accidental)]

            pitch_img = ImageChops.multiply(pitch_img, image_dict[pitch_idx])
            if octave is not None:
                pitch_img = ImageChops.multiply(pitch_img, image_dict[octave])
            if accidental is not None:
                pitch_img = ImageChops.multiply(pitch_img, image_dict[accidental])

            whole_img.paste(image_dict[additional_symbol], (0, 0))
            whole_img.paste(pitch_img, (0, width))

        if lyric is not None:
            text_draw = ImageDraw.Draw(whole_img)
            text_draw.text((10, width*2), lyric, fill=(0, 0, 0), font=font)

        return whole_img

    def construct_notation_image(stream, image_dict) -> tuple:
        image_width = determine_image_width(stream)
        image_height = len(line_break_idxs)+1

        current_row_counter = 0

        boxes = []

        if image_width * image_height <= 0:
            return Image.new('RGB', (width, width * 4), (255, 255, 255)), boxes

        whole_image = Image.new('RGB', (width * image_width, image_height * width * 4), (255, 255, 255))

        for measure in stream:
            idx = 0
            for note in measure:
                current_img = note_to_suzipu(font, note, image_dict)
                whole_image.paste(current_img, (width * idx, current_row_counter * width * 4))
                boxes.append(((width * idx, current_row_counter * width * 4), (width + width * idx, current_row_counter * width * 4 + 3 * width)))
                if note.line_break:
                    current_row_counter += 1
                    idx = 0
                else:
                    idx += 1
        return whole_image, boxes

    stream = construct_note_stream(music_list, lyrics_list, line_break_idxs)
    stream = stream.transpose(fingering.transposition_index)

    fingering_img = construct_fingering_image(font, image_dict, fingering)
    notation_image, boxes = construct_notation_image(stream, image_dict)

    whole_image = vertical_composition([fingering_img, notation_image])

    boxes = apply_border_to_boxes(boxes, 0, fingering_img.height)

    if return_boxes:
        return whole_image, boxes
    return whole_image


def common_notation_to_western(font, image_dict, mode, music_list, lyrics_list, line_break_idxs=[], fingering=Fingering.ALL_CLOSED_AS_1, return_boxes=False):
    pitch_past = []
    width = 65

    if mode:
        try:
            music_list = mode.convert_pitches_in_list(music_list)
        except TypeError:  # This happens when the chosen mode dows not match the piece
            return None

    def note_to_western(font, note, image_dict):
        def note_to_offset_and_staff_type(note):
            def throw_error():
                raise IndexError(f"Out of range. The note to be displayed {note} is not between A3 and C6")

            pitch_octave = note.pitch.octave
            pitch_step = note.pitch.step

            class StaffType:
                DOUBLE_LOW = "double_low"
                LOW = "low"
                NORMAL = "normal"
                HIGH = "high"
                DOUBLE_HIGH = "double_high"

            if pitch_octave == 3:
                if pitch_step == "A": return 88, StaffType.DOUBLE_LOW
                elif pitch_step == "B": return 83, StaffType.LOW
                else: throw_error()
            elif pitch_octave == 4:
                if pitch_step == "C": return 77, StaffType.LOW
                elif pitch_step == "D": return 72, StaffType.NORMAL
                elif pitch_step == "E": return 66, StaffType.NORMAL
                elif pitch_step == "F": return 61, StaffType.NORMAL
                elif pitch_step == "G": return 55, StaffType.NORMAL
                elif pitch_step == "A": return 50, StaffType.NORMAL
                elif pitch_step == "B": return 44, StaffType.NORMAL
                else: throw_error()
            elif pitch_octave == 5:
                if pitch_step == "C": return 39, StaffType.NORMAL
                elif pitch_step == "D": return 33, StaffType.NORMAL
                elif pitch_step == "E": return 28, StaffType.NORMAL
                elif pitch_step == "F": return 22, StaffType.NORMAL
                elif pitch_step == "G": return 17, StaffType.NORMAL
                elif pitch_step == "A": return 11, StaffType.HIGH
                elif pitch_step == "B": return 6, StaffType.HIGH
                else: throw_error()
            elif pitch_octave == 6:
                if pitch_step == "C": return 0, StaffType.DOUBLE_HIGH
            else:
                throw_error()

        whole_img = Image.new('RGB', (width, width + 120 + width), (255, 255, 255))
        notation_img = Image.new('RGB', (width, 120), (255, 255, 255))
        notehead_img = Image.new('RGB', (width, 30), (255, 255, 255))
        lyric = note.lyric

        if note.isRest:
            pass
        else:
            note.pitch.updateAccidentalDisplay(pitchPast=pitch_past)
            pitch_past.append(note.pitch)

            additional_symbol = additional_symbol_dictionary[note.additional_symbol]
            accidental = accidental_dictionary[repr(note.pitch.accidental)]

            offset, staff_type = note_to_offset_and_staff_type(note)

            notehead_img = ImageChops.multiply(notehead_img, image_dict["notehead"])
            if accidental is not None:
                notehead_img = ImageChops.multiply(notehead_img, image_dict[accidental])

            notation_img.paste(notehead_img, (0, offset))
            notation_img = ImageChops.multiply(notation_img, image_dict[staff_type])

            whole_img.paste(image_dict[additional_symbol], (0, 0))
            whole_img.paste(notation_img, (0, width))

        if lyric is not None:
            text_draw = ImageDraw.Draw(whole_img)
            text_draw.text((10, width + 120), lyric, fill=(0, 0, 0), font=font)

        return whole_img

    def construct_notation_image(stream, image_dict):
        image_width = determine_image_width(stream) + 1
        image_height = len(line_break_idxs)+1

        boxes = []

        current_row_counter = 0
        whole_image = Image.new('RGB', (width * image_width, image_height * (width + 120 + width + width)), (255, 255, 255))
        for measure in stream:
            idx = 0
            for note in measure:
                current_img = note_to_western(font, note, image_dict)
                whole_image.paste(current_img, (width * (idx + 1), current_row_counter * (width + 120 + width + width)))
                boxes.append(((width * (idx + 1), current_row_counter * (width + 120 + width + width)), (width * (idx + 2), (current_row_counter + 1) * (width + 120 + width + width) - width)))
                if note.line_break:
                    whole_image.paste(image_dict["clef"], (0, current_row_counter * (width + 120 + width + width) + width))
                    current_row_counter += 1
                    idx = 0
                else:
                    idx += 1
            whole_image.paste(image_dict["clef"], (0, current_row_counter * (width + 120 + width + width) + width))
        return whole_image, boxes

    stream = construct_note_stream(music_list, lyrics_list, line_break_idxs)
    stream = stream.transpose(fingering.transposition_index)

    if fingering_to_lowest_note(fingering) < music21.note.Note("Ab3"):
        stream = stream.transpose("P8")  # transpose too deep into normal range

    fingering_img = construct_transposition_image(font, image_dict, fingering)
    notation_image, boxes = construct_notation_image(stream, image_dict)

    boxes = apply_border_to_boxes(boxes, 0, fingering_img.height)

    whole_image = vertical_composition([fingering_img, notation_image])

    if return_boxes:
        return whole_image, boxes
    return whole_image


def _notation_to_textbased(font, notation_font, music_list, lyrics_list, note_to_textbased_function, line_break_idxs=[], return_boxes=False, is_vertical=False):
    width = 65

    def switch_coordinates(box):
        if is_vertical:
            return box[1], box[0]
        return box[0], box[1]

    def note_to_textbased(font, note):
        whole_img = Image.new('RGB', switch_coordinates((width, 2 * width)), (255, 255, 255))

        lyric = note.lyric
        text_draw = ImageDraw.Draw(whole_img)

        if note.isRest:
            pass
        else:
            notation = note_to_textbased_function(note.original_pitch)

            if is_vertical:
                if len(notation) == 1:
                    text_draw.text((85, 15), notation[0], fill=(0, 0, 0), font=notation_font)
                else:
                    text_draw.text((70, 15), notation[0], fill=(0, 0, 0), font=notation_font)
                    text_draw.text((95, 15), notation[1], fill=(0, 0, 0), font=notation_font)
                if lyric is not None:
                    text_draw.text((15, 0), lyric, fill=(0, 0, 0), font=font)
            else:
                if len(notation) == 1:
                    text_draw.text((17, 30), notation[0], fill=(0, 0, 0), font=notation_font)
                else:
                    text_draw.text((17, 0), notation[0], fill=(0, 0, 0), font=notation_font)
                    text_draw.text((17, 30), notation[1], fill=(0, 0, 0), font=notation_font)
                if lyric is not None:
                    text_draw.text((10, width), lyric, fill=(0, 0, 0), font=font)

        return whole_img

    def construct_notation_image(stream) -> tuple:
        image_width = determine_image_width(stream)
        image_height = len(line_break_idxs) + 1

        current_row_counter = 0

        boxes = []

        if image_width * image_height <= 0:
            return Image.new('RGB', switch_coordinates((width, width * 3)), (255, 255, 255)), boxes

        whole_image_width = width * image_width
        whole_image_height = image_height * width * 3
        whole_image = Image.new('RGB', switch_coordinates((whole_image_width, whole_image_height)), (255, 255, 255))

        for measure in stream:
            idx = 0
            for note in measure:
                if is_vertical:
                    current_img = note_to_textbased(font, note)
                    whole_image.paste(current_img, switch_coordinates((width * idx, whole_image_height - 3*width - current_row_counter * width * 3)))
                    boxes.append((switch_coordinates((width * idx, whole_image_height - 3*width - current_row_counter * width * 3)),
                                  switch_coordinates((width + width * idx, whole_image_height - 3*width - current_row_counter * width * 3 + 2 * width))))
                else:
                    current_img = note_to_textbased(font, note)
                    whole_image.paste(current_img, switch_coordinates((width * idx, current_row_counter * width * 3)))
                    boxes.append((switch_coordinates((width * idx, current_row_counter * width * 3)),
                                  switch_coordinates((width + width * idx, current_row_counter * width * 3 + 2 * width))))
                if note.line_break:
                    current_row_counter += 1
                    idx = 0
                else:
                    idx += 1
        return whole_image, boxes

    stream = construct_note_stream(music_list, lyrics_list, line_break_idxs)

    notation_image, boxes = construct_notation_image(stream)

    if return_boxes:
        return notation_image, boxes
    return notation_image


def notation_to_gongchepu(font, gongche_font, music_list, lyrics_list, line_break_idxs=[], return_boxes=False, is_vertical=False):
    return _notation_to_textbased(font, gongche_font, music_list, lyrics_list, GongcheMelodySymbol.to_gongche, line_break_idxs, return_boxes, is_vertical)


def notation_to_lvlvpu(font, lvlv_font, music_list, lyrics_list, line_break_idxs=[], return_boxes=False, is_vertical=False):
    return _notation_to_textbased(font, lvlv_font, music_list, lyrics_list, GongcheMelodySymbol.to_lvlv, line_break_idxs, return_boxes, is_vertical)


def notation_to_suzipu(font, image_dict, music_list, lyrics_list, line_break_idxs=[], return_boxes=False, is_vertical=False):
    width = 65

    def switch_coordinates(box):
        if is_vertical:
            return box[1], box[0]
        return box[0], box[1]

    def note_to_suzipu(font, note):
        whole_img = Image.new('RGB', switch_coordinates((width, 2 * width)), (255, 255, 255))
        whole_img_copy = Image.new('RGB', switch_coordinates((width, 2 * width)), (255, 255, 255))

        lyric = note.lyric

        if note.isRest:
            pass
        else:
            original_pitch = None
            if note.original_pitch is not None:
                try:
                    original_pitch = suzipu_to_info(note.original_pitch).name.lower().replace(" ", "_")
                except AttributeError:
                    pass

            additional_symbol = None
            if note.additional_symbol is not None:
                try:
                    additional_symbol = suzipu_to_info(note.additional_symbol).name.lower()
                except AttributeError:
                    pass

            if is_vertical:
                if original_pitch is not None and additional_symbol is not None:
                    whole_img.paste(image_dict[original_pitch], (80, 7))
                    whole_img_copy.paste(image_dict[additional_symbol], (80, 27))
                    whole_img = ImageChops.multiply(whole_img, whole_img_copy)
                else:
                    symbol = original_pitch if original_pitch is not None else additional_symbol
                    whole_img.paste(image_dict[symbol], (80, 17))
                if lyric is not None:
                    text_draw = ImageDraw.Draw(whole_img)
                    text_draw.text((15, 0), lyric, fill=(0, 0, 0), font=font)
            else:
                if original_pitch is not None and additional_symbol is not None:
                    whole_img.paste(image_dict[original_pitch], (17, 10))
                    whole_img_copy.paste(image_dict[additional_symbol], (17, 30))
                    whole_img = ImageChops.multiply(whole_img, whole_img_copy)
                else:
                    symbol = original_pitch if original_pitch is not None else additional_symbol
                    whole_img.paste(image_dict[symbol], (17, 20))
                if lyric is not None:
                    text_draw = ImageDraw.Draw(whole_img)
                    text_draw.text((10, width), lyric, fill=(0, 0, 0), font=font)


        return whole_img

    def construct_notation_image(stream) -> tuple:
        image_width = determine_image_width(stream)
        image_height = len(line_break_idxs) + 1

        current_row_counter = 0

        boxes = []

        if image_width * image_height <= 0:
            return Image.new('RGB', switch_coordinates((width, width * 3)), (255, 255, 255)), boxes

        whole_image_width = width * image_width
        whole_image_height = image_height * width * 3
        whole_image = Image.new('RGB', switch_coordinates((whole_image_width, whole_image_height)), (255, 255, 255))

        for measure in stream:
            idx = 0
            for note in measure:
                if is_vertical:
                    current_img = note_to_suzipu(font, note)
                    whole_image.paste(current_img, switch_coordinates((width * idx, whole_image_height - width * 3 - current_row_counter * width * 3)))
                    boxes.append((switch_coordinates((width * idx, whole_image_height - width * 3 - current_row_counter * width * 3)),
                                  switch_coordinates((width + width * idx, whole_image_height - width * 3 - current_row_counter * width * 3 + 2 * width))))
                else:
                    current_img = note_to_suzipu(font, note)
                    whole_image.paste(current_img, switch_coordinates((width * idx, current_row_counter * width * 3)))
                    boxes.append((switch_coordinates((width * idx, current_row_counter * width * 3)),
                                  switch_coordinates(
                                      (width + width * idx, current_row_counter * width * 3 + 2 * width))))
                if note.line_break:
                    current_row_counter += 1
                    idx = 0
                else:
                    idx += 1
        return whole_image, boxes

    stream = construct_note_stream(music_list, lyrics_list, line_break_idxs)

    notation_image, boxes = construct_notation_image(stream)

    if return_boxes:
        return notation_image, boxes
    return notation_image


def write_to_musicxml(file_path, suzipu_list, lyrics_list, fingering=Fingering.ALL_CLOSED_AS_1, title="", mode="", preface=""):
    stream = construct_note_stream_musicxml(suzipu_list, lyrics_list)
    stream = stream.transpose(fingering.transposition_index)

    if fingering_to_lowest_note(fingering) < music21.note.Note("Ab3"):
        stream = stream.transpose("P8")  # transpose too deep into normal range

    for note in stream.flat.notes:
        print(note)

    stream.insert(0, music21.metadata.Metadata())
    stream.metadata["title"] = [title, mode, preface]

    stream.write("musicxml", fp=file_path)

    return None


def construct_metadata_image(title_font, text_font, title, mode, preface, image_width=None, is_vertical=False, composer=None):
    def adjust_to_vertical(string: str):
        string = string.replace("，", "︐")
        string = string.replace(",", "︐")
        string = string.replace("、", "︑")
        string = string.replace("。", "︒")
        string = string.replace(".", "︒")

        string = string.replace("「", "﹁")
        string = string.replace("」", "﹂")
        string = string.replace("“", "﹁")
        string = string.replace("”", "﹂")
        string = string.replace("『", "﹃")
        string = string.replace("』", "﹄")

        string = string.replace("（", "︵")
        string = string.replace("）", "︶")
        string = string.replace("(", "︵")
        string = string.replace(")", "︶")
        string = string.replace("【", "︻")
        string = string.replace("】", "︼")
        string = string.replace("《", "︽")
        string = string.replace("》", "︾")


        string = string.replace(":", "︓")
        string = string.replace("：", "︓")
        string = string.replace(";", "︔")
        string = string.replace("；", "︔")
        string = string.replace("!", "︕")
        string = string.replace("！", "︕")
        string = string.replace("?", "︖")
        string = string.replace("？", "︖")

        string = string.replace("(", "︵")
        string = string.replace(")", "︶")

        string = string.replace("...", "︙")
        string = string.replace("…", "︙")

        return string

    if is_vertical:
        title = adjust_to_vertical(title)
        mode = adjust_to_vertical(mode)
        preface = adjust_to_vertical(preface)

    def calculate_text_properties(mode, preface):
        text_lines = []
        if composer is not None:
            text_lines += composer.split("\n") + ["\n"]
        elif is_vertical:
            text_lines += ["\n"]
        text_lines += mode.split("\n") + ["\n"]
        text_lines += preface.split("\n") + ["\n"]

        max_width = -1
        for line in text_lines:
            max_width = max(len(line), max_width)

        return text_lines, max_width

    text_lines, max_width = calculate_text_properties(mode, preface)

    if image_width < max_width * 40:
        image_width = max_width * 40

    if is_vertical:
        max_len = 0
        for line in text_lines:
            max_len = max(len(line), max_len)

        min_height = max(80*len(title) + len(composer)*60 + 40, 60*max_len + 40)
        image_height = min_height

        image_width = len(text_lines)*70

        whole_image = Image.new('RGB', (image_width, image_height), (255, 255, 255))

        text_draw = ImageDraw.Draw(whole_image)

        offset = 0
        for idx, title_char in enumerate(title):
            offset = 80 * idx
            text_draw.text((image_width - 80, offset), title_char, fill=(0, 0, 0), font=title_font)

        for idx, first_line_char in enumerate(text_lines[0]):
            text_draw.text((image_width - 55, offset + 100 + 60*idx), first_line_char, fill=(0, 0, 0), font=text_font)

        for line_idx, line in enumerate(text_lines[1:]):
            for idx, character in enumerate(line):
                text_draw.text((image_width - 120 - line_idx*70, 20+60*idx), character, fill=(0, 0, 0), font=text_font)

    else:
        image_height = 160 + len(text_lines) * 70

        whole_image = Image.new('RGB', (image_width, image_height), (255, 255, 255))

        text_draw = ImageDraw.Draw(whole_image)

        _, _, w, h = text_draw.textbbox((0, 0), title, font=title_font)
        text_draw.text(((image_width - w) / 2, 0), title, fill=(0, 0, 0), font=title_font)

        for line_idx, line in enumerate(text_lines):
            _, _, w, h = text_draw.textbbox((0, 0), line, font=text_font)
            text_draw.text(((image_width - w) / 2, 120 + line_idx * 70), line, fill=(0, 0, 0), font=text_font)

    return whole_image


def construct_fingering_image(font, image_dict, fingering: FingeringProperties):
    whole_image = Image.new('RGB', (30 * 10, 130), (255, 255, 255))

    text_draw = ImageDraw.Draw(whole_image)

    degree, octave, accidental = fingering.image_data
    fingering_mark = ImageChops.multiply(image_dict[degree], image_dict[octave])

    if accidental is not None:
        fingering_mark = ImageChops.multiply(fingering_mark, image_dict[accidental])

    fingering_mark = fingering_mark.resize((50, 50))

    whole_image.paste(fingering_mark, (6 * 30, 20))
    text_draw.text((0, 15), "（筒音作       ）", fill=(0, 0, 0), font=font)

    return whole_image


def construct_transposition_image(font, image_dict, fingering):
    whole_image = Image.new('RGB', (30 * 10, 130), (255, 255, 255))

    text_draw = ImageDraw.Draw(whole_image)

    he_mark = image_dict["he"]

    he_mark = he_mark.resize((50, 50))

    whole_image.paste(he_mark, (40, 20))
    text_draw.text((0, 15), f"（       =  {fingering_to_lowest_note(fingering).pitch}）", fill=(0, 0, 0), font=font)

    return whole_image


if __name__ == "__main__":
    args = parse_arguments()
    suzipu_list = json.loads(args.suzipu_list)
    lyrics_list = json.loads(args.lyrics_list)
    line_break_idxs = json.loads(args.line_break_idxs)
    title = args.title
    mode = args.mode
    preface = args.preface
    #parse_notation_and_write_to_file(music_list, lyrics_list, args.output_file_path)
    big_font = load_font(70)
    small_font = load_font(40)

    MODE = GongdiaoModeList.XIAN_LV_DIAO
    suzipu_list = MODE.convert_pitches_in_list(suzipu_list)


    #notation_img = common_notation_to_jianpu(small_font, load_jianpu_image_dict(), MODE, music_list, lyrics_list, line_break_idxs, Fingering.ALL_CLOSED_AS_6)
    notation_img = common_notation_to_western(small_font, load_western_image_dict(), MODE, suzipu_list, lyrics_list, line_break_idxs, Fingering.ALL_CLOSED_AS_6)
    metadata_img = construct_metadata_image(big_font, small_font, title, mode, preface, image_width=notation_img.width)

    combined_img = vertical_composition([metadata_img, notation_img])
    combined_img = add_border(combined_img, 150, 200)
    combined_img.save("image_to_draw.png")
