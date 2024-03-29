import dataclasses
import os
import tkinter as tk

import PIL
import cv2
from PIL import ImageTk

from src.auxiliary import BoxType, JsonSerializable, SetInt, BoxesWithType, ListCycle, BoxManipulationAction, \
    get_folder_contents, get_image_from_box_ai_assistant, get_image_from_box
from src.hr_segmentation_adapter import predict_boxes
from src.plugins.suzipu_lvlvpu_gongchepu.notes_to_image import NotationResources
from src.plugins import NotationTypePlugins


@dataclasses.dataclass
class PieceProperties(JsonSerializable):
    notation_type: str = NotationTypePlugins()
    number_of_pages: int = 1
    mode_properties: dict = dataclasses.field(default_factory=dict)
    base_image_path: str = dataclasses.field(default=None)
    content: BoxesWithType = dataclasses.field(default=BoxesWithType())
    version: str = "2.0"
    composer: str = ""

    @classmethod
    def load(cls, data: dict) -> "Self":
        def content_to_boxes_format(content):
            content_list = []

            idx = 0
            while idx < len(content):
                if content[idx]["box_type"] == BoxType.MUSIC:
                    music_list = []
                    lyrics_list = []

                    while idx < len(content) and content[idx]["box_type"] == BoxType.MUSIC:
                        music_list.append({
                            "box_type": BoxType.MUSIC,
                            "coordinates": content[idx]["notation_coordinates"],
                            "annotation": content[idx]["notation_content"],
                            "is_excluded_from_dataset": content[idx]["is_excluded_from_dataset"],
                            "is_line_break": content[idx]["is_line_break"]
                        })
                        lyrics_list.append({
                            "box_type": BoxType.LYRICS,
                            "coordinates": content[idx]["text_coordinates"],
                            "annotation": content[idx]["text_content"],
                            "is_excluded_from_dataset": content[idx]["is_excluded_from_dataset"],
                            "is_line_break": content[idx]["is_line_break"]
                        })
                        if content[idx]["is_line_break"] or idx == len(content)-1:
                            content_list += music_list
                            content_list += lyrics_list
                            idx += 1
                            break
                        idx += 1
                else:
                    content_list.append({
                                "box_type": content[idx]["box_type"],
                                "coordinates": content[idx]["text_coordinates"],
                                "annotation": content[idx]["text_content"],
                                "is_excluded_from_dataset": content[idx]["is_excluded_from_dataset"],
                                "is_line_break": content[idx]["is_line_break"]
                            })
                    idx += 1
            return content_list

        images = data["images"]
        data["base_image_path"] = images[0]
        data["number_of_pages"] = len(images)
        del data["images"]

        instance = super().load(data)
        instance.content = BoxesWithType(content_to_boxes_format(data["content"]))
        instance.mode_properties = instance.mode_properties

        return instance

    def dump(self) -> dict:
        dictionary = dataclasses.asdict(self)
        dictionary["content"] = dictionary["content"]["boxes_list"]
        dictionary["mode_properties"] = self.mode_properties
        return dictionary


class GuiState:
    def __init__(self, main_window, weights_path):
        self.main_window = main_window
        self.segmentation_weights_path = weights_path  # weights path for segmentation algorithm

        self.images_dir = "./res/annotation_start_directory"
        '''Directory in which the images for the project are'''
        self.output_dir = "."
        '''Directory where the last file was saved'''
        self.initial_filename = "untitled"
        '''Filename of the last saved file'''
        self.empty_image = ImageTk.PhotoImage(image=PIL.Image.new("RGB", (80, 80), (255, 255, 255)))
        '''Empty annotation image'''

        self.current_image = None
        '''Currently displayed image'''
        self.current_annotation_image = None
        '''Image belonging to currently selected box'''
        self.current_box_annotation = ""
        '''The annotation of the current box'''
        self.image_name_circle: ListCycle = None
        '''ListCycle containing the list of images in the project folder and the currently selected one'''
        self.images = []  # The list of images which are active for the current project (i.e., the n pages the piece has)

        self.must_be_changed = None # TODO refactor
        '''If this is true, the program state has changed and this triggers some actions'''
        self.type_to_cycle_dict = {}
        '''Dict saving the ListCycle for the boxing belonging to the type. type_to_cycle_dict[TYPE] = ListCycle'''

        self.notation_resources = NotationResources()  # TODO: must be changed since plugin dependent
        self.number_of_pages = SetInt(1)
        self.draw_box_width = SetInt(1)
        '''the number of image files the piece uses'''
        self.box_idx_to_tkinter_image_dict = {}
        '''dict[global box idx] -> the tkinter image corresponding to this box'''

        # TK variables for dynamic information easily accessible by the widgets
        self.tk_display_images_in_reversed_order = tk.BooleanVar(self.main_window, True)
        '''If true, the pages are displayed in traditional Chinese order, i.e., from right to left'''
        self.tk_segmentation_individual_pages = tk.BooleanVar(self.main_window, True)
        '''If true, the individual pages are segmented individually instead of segmenting the merged image'''
        self.tk_current_filename = tk.StringVar(self.main_window)
        '''Currently selected image file name'''

        self.tk_current_action = tk.StringVar(self.main_window, BoxManipulationAction.NO_ACTION)
        '''The currently selected box manipulation action'''

        self.tk_current_composer = tk.StringVar(self.main_window, "")
        '''The name of currently selected composer'''
        self.tk_notation_plugin_selection = tk.StringVar(self.main_window, "")
        '''The type of currently selected notation plugin'''
        self.tk_current_boxtype = tk.StringVar(self.main_window, dataclasses.astuple(BoxType())[0])
        '''The type of currently selected box'''
        self.tk_current_box_out_of_current_type = tk.StringVar(self.main_window, "")
        '''String in the form of "<current box idx> / <number of all boxes of this type>"'''
        self.tk_num_all_boxes_of_current_type = tk.StringVar(self.main_window, "")
        '''Number of all boxes of currently selected type'''
        self.tk_current_box_annotation = tk.StringVar(self.main_window, "")
        '''The annotation of the current box'''
        self.tk_current_box_is_excluded = tk.BooleanVar(self.main_window, False)
        '''True if the current box is excluded from OMR dataset'''
        self.tk_current_box_is_line_break = tk.BooleanVar(self.main_window,False)
        '''True if the current box has a line break'''
        self.tk_current_mode_string = tk.StringVar(self.main_window, "")
        '''The string of the currently selected musical mode'''


class ProgramState:
    def __init__(self, piece_properties: PieceProperties, gui_state: GuiState):
        self.piece_properties = piece_properties
        self.gui_state = gui_state
        self.initialize_from_piece_properties(self.piece_properties)

    def initialize_from_piece_properties(self, piece_properties):
        self.piece_properties = piece_properties
        self.gui_state.image_name_circle = ListCycle(get_folder_contents(self.gui_state.images_dir, only_images=True))
        self.gui_state.must_be_changed = False
        self.gui_state.number_of_pages.set(self.piece_properties.number_of_pages)

    def get_current_type(self):
        return self.gui_state.tk_current_boxtype.get()

    def get_current_type_cycle(self) -> ListCycle:
        return self.gui_state.type_to_cycle_dict[self.get_current_type()]

    def get_first_page_image_name(self):
        return os.path.basename(self.gui_state.image_name_circle.get_current())

    def get_current_annotation_index(self):
        try:
            if self.gui_state.tk_current_action.get() == BoxManipulationAction.ANNOTATE:
                return self.get_current_type_cycle().get_current()
            return None
        except Exception:
            return None

    def get_current_local_annotation_index(self):
        try:
            return self.get_current_type_cycle().current_position
        except Exception:
            return None

    def get_current_annotation(self):
        index = self.get_current_annotation_index()
        if index is not None:
            return self.piece_properties.content.get_index_annotation(index)
        return None

    def set_current_annotation(self, annotation):
        if self.gui_state.tk_current_action.get() == BoxManipulationAction.ANNOTATE:
            self.piece_properties.content.set_index_annotation(
                self.get_current_annotation_index(), annotation)

    def update_annotation_image_and_variables(self):
        current_idx = self.get_current_annotation_index()

        if current_idx is not None:
            try:
                if len(self.get_current_type_cycle()):
                    self.gui_state.current_annotation_image = self.gui_state.box_idx_to_tkinter_image_dict[current_idx]
                    self.gui_state.tk_current_box_out_of_current_type.set(
                        f"{self.get_current_type_cycle().current_position + 1} / {len(self.get_current_type_cycle())}")
                    self.gui_state.tk_num_all_boxes_of_current_type.set(
                        f"{len(self.get_current_type_cycle())}")
            except KeyError as e:
                print(f"Could not retrieve image with index {current_idx}. {e}")

            current_box_annotation = self.piece_properties.content.get_index_annotation(current_idx)

            # very important! we must load the box excludedness first, because the change of self.gui_state.gui_state.tk_current_box_annotation
            # triggers the saving routine!
            self.gui_state.tk_current_box_is_excluded.set(
                self.piece_properties.content.is_index_excluded(current_idx))
            self.gui_state.tk_current_box_is_line_break.set(
                self.piece_properties.content.is_index_line_break(current_idx))

            self.gui_state.current_box_annotation = current_box_annotation

    def fill_all_boxes_of_type(self, box_type, iterable, constant_fill=False):
        if self.gui_state.tk_current_action.get() == BoxManipulationAction.ANNOTATE:
            for idx, box_index in enumerate(self.gui_state.type_to_cycle_dict[box_type].list):
                if constant_fill:
                    self.piece_properties.content.set_index_annotation(box_index, iterable)
                else:
                    self.piece_properties.content.set_index_annotation(box_index, iterable[idx])

    def fill_all_boxes_of_current_type(self, iterable):
        self.fill_all_boxes_of_type(self.gui_state.tk_current_boxtype.get(), iterable)

    def get_contents_of_type(self, key: str):
        try:
            return [self.piece_properties.content.get_index_annotation(box_idx) for box_idx in
                    self.gui_state.type_to_cycle_dict[key].list]
        except AttributeError:
            return None

    def get_mode_string(self):
        string = ""
        for character in self.get_contents_of_type(BoxType.MODE):
            string += character
        return string

    def get_box_images_from_type(self, key: str):
        try:
            coordinates = [self.piece_properties.content.get_index_coordinates(box_idx) for box_idx in self.gui_state.type_to_cycle_dict[key].list]
            images = [get_image_from_box_ai_assistant(self.gui_state.current_image, coord) for coord in coordinates]
            return images
        except AttributeError as e:
            return None

    def get_raw_box_images_from_type(self, key: str):
        try:
            coordinates = [self.piece_properties.content.get_index_coordinates(box_idx) for box_idx in self.gui_state.type_to_cycle_dict[key].list]
            images = [get_image_from_box(self.gui_state.current_image, coord) for coord in coordinates]
            return images
        except AttributeError as e:
            return None
    
    def construct_image(self):
        self.piece_properties.base_image_path = self.gui_state.image_name_circle.get_current()
        self.gui_state.images = []

        if self.gui_state.number_of_pages.get() > 0:
            for idx in range(0, self.gui_state.number_of_pages.get()):
                image_name = self.gui_state.image_name_circle.get_nth_from_current(idx)
                self.gui_state.images.append(cv2.cvtColor(cv2.imread(image_name), cv2.COLOR_BGR2RGB))

            max_width, max_height = 0, 0
            for image in self.gui_state.images:
                max_height = max(image.shape[0], max_height)
                max_width = max(image.shape[1], max_width)

            for idx in range(len(self.gui_state.images)):
                self.gui_state.images[idx] = cv2.copyMakeBorder(
                    src=self.gui_state.images[idx],
                    top=0,
                    bottom=max_height - self.gui_state.images[idx].shape[0],
                    left=0,
                    right=max_width - self.gui_state.images[idx].shape[1],
                    borderType=cv2.BORDER_CONSTANT,
                    value=[255, 255, 255]
                )

            if self.gui_state.tk_display_images_in_reversed_order.get():
                self.gui_state.images.reverse()

            self.gui_state.current_image = cv2.hconcat(self.gui_state.images)
            self.gui_state.tk_current_filename.set(self.get_first_page_image_name())
            self.gui_state.must_be_changed = False

    def make_new_segmentation(self):
        def shift_coordinates_by_width(coordinate_list, offset):
            l = []
            for element in coordinate_list:
                l.append(((element[0][0] + offset, element[0][1]), (element[1][0] + offset, element[1][1])))
            return l

        self.piece_properties.content.reset()

        def wait(message):
            win = tk.Toplevel()
            win.title('Wait')
            new_label = tk.Label(win, text=message, padx=10, pady=10)
            new_label.pack()
            return win

        def segment():
            if self.gui_state.tk_segmentation_individual_pages.get():
                current_width_offset = 0
                boxes = []
                for img in self.gui_state.images:
                    current_box = predict_boxes(img, self.gui_state.segmentation_weights_path)
                    current_box = shift_coordinates_by_width(current_box, current_width_offset)
                    boxes += current_box
                    current_width_offset += img.shape[1]

                self.piece_properties.content.create_from_coordinate_list(boxes)
            else:
                self.piece_properties.content.create_from_coordinate_list(
                    predict_boxes(self.gui_state.current_image,
                                  self.gui_state.segmentation_weights_path))

        win = wait("Segmentation in progress. Please wait...")
        self.gui_state.main_window.wait_visibility(win)
        win.update()
        segment()
        win.destroy()
