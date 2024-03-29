import dataclasses
import importlib
import os

import PIL
import cv2
import numpy as np
from PIL import Image, ImageTk


def draw_transparent_rectangle(image, rect0, rect1, color, thickness, alpha=0.7):
    overlay = image.copy()
    overlay = cv2.rectangle(overlay, rect0, rect1,
                            color, thickness)
    image = cv2.addWeighted(overlay, alpha, image, 1-alpha, 0)
    return image


def get_folder_contents(path, only_images=False):
    try:
        l = []
        for file_name in sorted(os.listdir(path)):
            if only_images and os.path.splitext(file_name)[-1] in [".png", ".jpeg", ".jpg", ".tiff", ".tif"]:
                l.append(os.path.join(path, file_name))
        return l
    except Exception as e:
        print(f"Could not read files from directory {path}. {e}")


def pil_to_cv(pil_image):
    open_cv_image = np.array(pil_image)
    return open_cv_image[:, :, ::-1].copy()


def state_to_json(program_state, gui_state):
    program_state_json = program_state.dump()
    content = program_state_json["content"]

    new_content = []
    music_list = []
    lyrics_list = []

    for box in content:
        if box["box_type"] == BoxType.MUSIC:
            music_list.append(box)
        elif box["box_type"] == BoxType.LYRICS:
            lyrics_list.append(box)
        else:
            new_content.append({
                "box_type": box["box_type"],
                "is_excluded_from_dataset": box["is_excluded_from_dataset"],
                "is_line_break": box["is_line_break"],
                "text_coordinates": box["coordinates"],
                "text_content": box["annotation"],
            })

    if len(music_list) != len(lyrics_list):
        raise AssertionError("File could not be saved: The number of music boxes must be equal to number of lyrics boxes.")

    for idx in range(len(music_list)):
        text_box = lyrics_list[idx]
        music_box = music_list[idx]

        plugin_name = gui_state.tk_notation_plugin_selection.get().lower()
        module = importlib.import_module(f"src.plugins.{plugin_name}")
        music_annotation = module.EMPTY_ANNOTATION if music_box["annotation"] == "" else music_box["annotation"]


        new_content.append({
            "box_type": BoxType.MUSIC,
            "is_excluded_from_dataset": music_box["is_excluded_from_dataset"],
            "is_line_break": text_box["is_line_break"],
            "text_coordinates": text_box["coordinates"],
            "text_content": text_box["annotation"],
            "notation_coordinates": music_box["coordinates"],
            "notation_content": music_annotation,
        })

    program_state_json["content"] = new_content

    # order the dictionary for better readability
    keyorder = ['version', 'notation_type', 'composer', 'mode_properties', 'images', 'content']
    program_state_json = {k: program_state_json[k] for k in keyorder if k in program_state_json}
    program_state_json["version"] = "2.0"

    return program_state_json


def rgb_to_bgr(rgb_tuple):
    return rgb_tuple[2], rgb_tuple[1], rgb_tuple[0]


def bgr_to_tkinter(bgr_tuple):
    b, g, r = bgr_tuple
    return f'#{r:02x}{g:02x}{b:02x}'


class Colors:
    RED = rgb_to_bgr((255, 80, 80))
    YELLOW = rgb_to_bgr((210, 210, 0))
    LIME = rgb_to_bgr((20, 255, 20))
    BLUE = rgb_to_bgr((100, 100, 255))
    CYAN = rgb_to_bgr((20, 255, 255))
    MAGENTA = rgb_to_bgr((255, 20, 255))
    VIOLET = rgb_to_bgr((168, 73, 256))


@dataclasses.dataclass
class BoxType:
    TITLE: str = "Title"
    MODE: str = "Mode"
    PREFACE: str = "Preface"
    MUSIC: str = "Music"
    LYRICS: str = "Lyrics"
    UNMARKED: str = "Unmarked"


def box_property_to_color(box_property: BoxType):
    box_property_to_color_dict = {
        BoxType.UNMARKED: Colors.RED,
        BoxType.TITLE: Colors.BLUE,
        BoxType.MODE: Colors.MAGENTA,
        BoxType.PREFACE: Colors.LIME,
        BoxType.MUSIC: Colors.CYAN,
        BoxType.LYRICS: Colors.YELLOW,
    }

    try:
        return box_property_to_color_dict[box_property]
    except KeyError as e:
        print(f"Could not find a color associated with value {box_property}. {e}")
        return Colors.RED


def is_point_in_rectangle(point, rectangle):
    return (rectangle[0][0] <= point[0] <= rectangle[1][0] or rectangle[1][0] <= point[0] <= rectangle[0][0])\
        and (rectangle[0][1] <= point[1] <= rectangle[1][1] or rectangle[1][1] <= point[1] <= rectangle[0][1])


def is_rectangle_big_enough(rectangle):
    return abs(rectangle[0][0] - rectangle[1][0]) > 5 and abs(rectangle[0][1] - rectangle[1][1]) > 5


def get_class_variables(classname):
    basic_list = vars(classname)
    return [basic_list[key] for key in basic_list.keys() if
            not callable(getattr(classname, key)) and not key.startswith("__")]


def get_image_from_box_fixed_size(current_image, box):
    (x1, y1), (x2, y2) = box
    x1, x2 = min(x1, x2), max(x1, x2)
    y1, y2 = min(y1, y2), max(y1, y2)

    cropped_img = current_image[y1:y2, x1:x2]
    blue, green, red = cv2.split(cropped_img)
    cropped_img = cv2.merge((red, green, blue))
    cropped_img = Image.fromarray(cropped_img)
    return_img = Image.new(cropped_img.mode, (80, 80), (255, 255, 255))
    return_img.paste(cropped_img, ((80 - cropped_img.size[0]) // 2, (80 - cropped_img.size[1]) // 2))
    return ImageTk.PhotoImage(image=return_img)


def cv_to_tkinter_image(cv_image):
    channel = cv_image[0, :, :]
    merge_img = cv2.merge((channel, channel, channel)).astype(np.uint8)
    merge_img = Image.fromarray(merge_img)
    return ImageTk.PhotoImage(image=merge_img)


def get_image_from_box_ai_assistant(current_image, box):
    (x1, y1), (x2, y2) = box
    x1, x2 = min(x1, x2), max(x1, x2)
    y1, y2 = min(y1, y2), max(y1, y2)

    image = current_image[y1:y2, x1:x2]
    image = 255 - image
    image = cv2.resize(image, (60, 60), interpolation=cv2.INTER_NEAREST)
    image = cv2.copyMakeBorder(image, 5, 5, 5, 5, cv2.BORDER_CONSTANT)
    image = 255 - image
    return image


def get_image_from_box(current_image, box):
    (x1, y1), (x2, y2) = box
    x1, x2 = min(x1, x2), max(x1, x2)
    y1, y2 = min(y1, y2), max(y1, y2)

    cropped_img = current_image[y1:y2, x1:x2, 0]
    return cropped_img


def open_file_as_tk_image(file_path):
    button_img = PIL.Image.open(file_path)
    # cropped_img = cropped_img.resize((40, 40))
    return ImageTk.PhotoImage(image=button_img)


@dataclasses.dataclass
class JsonSerializable:
    def dump(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def load(cls, data: dict) -> "Self":
        return cls(**data)


@dataclasses.dataclass
class SetInt(JsonSerializable):
    value: int

    def set(self, integer):
        try:
            self.value = int(integer)
        except TypeError:
            self.value = int(list(integer.values())[0])  # for compatibility with the old version, where this is represented as dict

    def increment(self):
        self.value += 1

    def decrement(self):
        self.value = max(self.value - 1, 1)

    def get(self):
        return self.value


@dataclasses.dataclass
class BoxesWithType(JsonSerializable):
    boxes_list: list[dict] = dataclasses.field(default_factory=lambda: [])

    @classmethod
    def create_new_box(cls, coordinates: tuple = tuple(), type: str =BoxType.UNMARKED, annotation=None, is_excluded_from_dataset: bool = False, is_line_break: bool = False):
        return {
            "coordinates": coordinates,
            "box_type": type,
            "annotation": annotation,
            "is_excluded_from_dataset": is_excluded_from_dataset,
            "is_line_break": is_line_break
        }

    def create_from_coordinate_list(self, coordinate_list):
        for coordinate in coordinate_list:
            self.boxes_list.append(self.create_new_box(coordinate))

    def reset(self):
        self.boxes_list = []

    def add_rectangle(self, point_1, point_2, type=BoxType.UNMARKED):
        self.boxes_list.append(self.create_new_box((point_1, point_2), type))

    def get_coordinates(self):
        coordinate_list = []
        for box in self.boxes_list:
            coordinate_list.append(box["coordinates"])
        return coordinate_list

    def get_line_break_indices(self):
        break_list = []
        for idx, box in enumerate(self.boxes_list):
            if box["is_line_break"]:
                break_list.append(idx)
        return break_list

    def get_index_coordinates(self, idx):
        return self.boxes_list[idx]["coordinates"]

    def get_index_type(self, idx):
        return self.boxes_list[idx]["box_type"]

    def get_index_annotation(self, idx):
        return self.boxes_list[idx]["annotation"]

    def is_index_excluded(self, idx):
        return self.boxes_list[idx]["is_excluded_from_dataset"]

    def is_index_line_break(self, idx):
        return self.boxes_list[idx]["is_line_break"]

    def set_index_coordinates(self, idx, coordinates):
        self.boxes_list[idx]["coordinates"] = coordinates

    def set_index_type(self, idx, type):
        self.boxes_list[idx]["box_type"] = type

    def set_index_annotation(self, idx, annotation):
        try:
            self.boxes_list[idx]["annotation"] = annotation
        except TypeError:  # idx == None
            pass

    def set_index_excluded(self, idx, boolean):
        self.boxes_list[idx]["is_excluded_from_dataset"] = boolean

    def set_index_line_break(self, idx, boolean):
        self.boxes_list[idx]["is_line_break"] = boolean

    def delete_index(self, idx):
        del self.boxes_list[idx]

    def sort(self):
        if len(self):
            def get_center_points(box):
                (x1, y1), (x2, y2) = box
                return int((x1 + x2) / 2), int((y1 + y2) / 2)

            center_points = []
            for idx in range(len(self)):
                coordinate = self.get_index_coordinates(idx)
                center_points.append([idx, get_center_points(coordinate)[0], get_center_points(coordinate)[1]])

            center_points.sort(key=lambda element: element[1], reverse=True)  # read from right to left
            center_points = np.array(center_points)
            split_indices = np.stack((np.arange(len(self) - 1), abs(center_points[1:, 1] - center_points[:-1, 1])),
                                     axis=1)

            split_indices = split_indices[split_indices[:, 1] > 20, :]
            split_indices = np.concatenate(([0], split_indices[:, 0] + 1, [None]))

            sorted_idxs = []
            line_break_idxs = []
            for idx in range(len(split_indices) - 1):
                idxs = center_points[split_indices[idx]:split_indices[idx + 1], :].tolist()
                idxs.sort(key=lambda element: element[2])  # read from top to bottom
                idxs = np.array(idxs)
                sorted_idxs += idxs[:, 0].tolist()
                line_break_idxs.append(sorted_idxs[-1])

            for idx in range(len(self)):
                self.set_index_line_break(idx, False)
            for idx in line_break_idxs[:-1]:
                self.set_index_line_break(idx, True)

            self.boxes_list = [self.boxes_list[idx] for idx in sorted_idxs]

    def __bool__(self):
        return self.boxes_list is not None

    def __len__(self):
        return len(self.boxes_list)

    def dump(self) -> dict:
        return self.boxes_list


class ListCycle:
    def __init__(self, l):
        self.list = l
        self.current_position = 0
        self.length = len(self.list)

    def next(self):
        self.current_position += 1
        self.current_position = self.current_position % self.length

    def previous(self):
        self.current_position -= 1
        self.current_position += self.length
        self.current_position = self.current_position % self.length

    def get_nth_from_current(self, n):
        position = self.current_position + n
        while position < 0:  # ensure positivity
            position += self.length
        position = position % self.length
        return self.list[position]

    def set_to_index(self, idx):
        try:
            if idx < self.length:
                self.current_position = idx
        except Exception as e:
            print(f"Cannot set ListCycle index to {idx}, since it only contains {self.length} elements. {e}")

    def get_current(self):
        try:
            return self.list[self.current_position]
        except Exception as e:
            return None

    def set_if_present(self, value):
        try:
            index = self.list.index(value)
            self.set_to_index(index)
        except ValueError as e:
            pass

    def __repr__(self):
        return f"ListCycle: {self.current_position} {self.list}"

    def __len__(self):
        return self.length


class BoxManipulationAction:
    NO_ACTION = "None"
    CREATE = "Create"
    MARK = "Mark"
    DELETE = "Delete"
    MOVE_RESIZE = "Move/Resize"
    ANNOTATE = "Annotate"
