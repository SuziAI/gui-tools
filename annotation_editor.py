import argparse
import copy
import dataclasses
import json

from pathlib import Path

import PIL
import cv2
import os

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.filedialog import asksaveasfilename
from tkinter.messagebox import showerror

from PIL import ImageTk
from PIL import Image

from src.auxiliary import ListCircle, BoxesWithType, is_point_in_rectangle, SetInt, SelectionMode, Colors, BoxProperty, \
    ProgramState, box_property_to_color, get_image_from_box_fixed_size, open_file_as_tk_image, is_rectangle_big_enough, \
    state_to_json, get_folder_contents, get_image_from_box_ai_assistant
from src.config import GO_INTO_ANNOTATION_MODE_IMAGE, INVALID_MODE_IMAGE
from src.widgets_auxiliary import on_closing, IncrementDecrementFrame, PreviousNextFrame, \
    SelectionFrame, SaveLoadFrame
from src.widgets_annotation import AnnotationFrame
from src.hr_segmentation_adapter import predict_boxes
from src.plugins.suzipu_lvlvpu_gongchepu.common import Symbol, GongdiaoModeList, AdditionalInfoFrame, DisplayNotesFrame
from src.notes_to_image import notation_to_jianpu, notation_to_western, NotationResources, \
    construct_metadata_image, vertical_composition, add_border, write_to_musicxml


class OpenCvWindow:
    def __init__(self, window_name):
        self.window_name = window_name
        self.current_click_coordinates = None
        self.is_clicked = False
        self.draw_image = None
        self.point_1 = None
        self.point_2 = None
        self.segmentation_boxes = BoxesWithType()

        cv2.namedWindow(self.window_name, cv2.WINDOW_GUI_NORMAL)
        cv2.resizeWindow(self.window_name, 600, 600)
        cv2.setMouseCallback(self.window_name, self.handle_mouse_events)

    def __del__(self):
        cv2.destroyWindow(self.window_name)

    def handle_mouse_events(self, event, x, y, flags, param):
        if event == cv2.EVENT_RBUTTONDOWN:
            self.is_clicked = True
            self.point_1 = (x, y)

        elif event == cv2.EVENT_MOUSEMOVE and self.is_clicked:
            self.current_click_coordinates = (x, y)

        elif event == cv2.EVENT_RBUTTONUP:
            self.is_clicked = False
            self.point_2 = (x, y)
            self.current_click_coordinates = None

    def draw_and_handle_clicks(self, program_state, selection_mode, boxtype, current_image, current_annotation_idx, set_current_annotation_idx = lambda: None):
        self.segmentation_boxes = program_state.content

        exit_flag = False
        self.draw_image = copy.deepcopy(current_image)

        keypress = cv2.waitKey(1)
        # exit if q is pressed or the red x button in the window
        if keypress == ord('q'): #or cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
            exit_flag = True

        if self.current_click_coordinates:
            if program_state.content:
                for idx, box in enumerate(program_state.content.get_coordinates()):
                    if is_point_in_rectangle(self.current_click_coordinates, box):
                        if selection_mode == SelectionMode.MARK:
                            program_state.content.set_index_type(idx, boxtype)
                        if selection_mode == SelectionMode.DELETE:
                            program_state.content.delete_index(idx)
                        if selection_mode == SelectionMode.ANNOTATE:
                            set_current_annotation_idx(idx)
            self.current_click_coordinates = None

        if selection_mode == SelectionMode.CREATE:
            if self.point_1 is not None and self.point_2 is not None:
                if is_rectangle_big_enough([self.point_1, self.point_2]):
                    self.segmentation_boxes.add_rectangle(self.point_1, self.point_2, type=boxtype)
                self.point_1 = None
                self.point_2 = None
        else:
            self.point_1 = None
            self.point_2 = None

        if program_state.content:
            for idx in range(len(program_state.content.get_coordinates())):
                start, end = program_state.content.get_index_coordinates(idx)
                if current_annotation_idx is not None and idx == current_annotation_idx:  #currently selected box should be drawn thicker
                    self.draw_image = cv2.rectangle(self.draw_image, start, end, Colors.VIOLET, 8)
                else:
                    self.draw_image = cv2.rectangle(self.draw_image, start, end, box_property_to_color(
                        program_state.content.get_index_type(idx)), 2)


        cv2.imshow(self.window_name, self.draw_image)
        return self.segmentation_boxes, exit_flag

    def get_current_draw_image(self):
        return self.draw_image


class MainWindow:
    def __init__(self, program_state: ProgramState, weights_path: str):
        self.program_state: ProgramState = None
        self.images_dir = "./res/annotation_start_directory"
        self.output_dir = "."
        self.image_name_circle: ListCircle = None
        self.must_be_changed = None
        self.images = []
        self.type_dict = {}
        self.empty_image = None
        self.notation_resources = NotationResources()
        self.initial_filename = "untitled"
        self.number_of_pages = SetInt(1)
        self.weights_path = weights_path

        self.initialize(program_state)

    def initialize(self, program_state):
        self.program_state = program_state
        self.image_name_circle = ListCircle(get_folder_contents(self.images_dir, only_images=True))
        self.must_be_changed = False
        self.number_of_pages.set(self.program_state.number_of_pages)

    def exec(self):
        def get_current_filename_from_circle(circle: ListCircle):
            return os.path.basename(circle.get_current())

        opencv_window = OpenCvWindow("Suzipu Musical Annotation Tool - Canvas")

        main_window = tk.Tk()
        main_window.title("Suzipu Musical Annotation Tool- Main Window")

        empty_image = PIL.Image.new("RGB", (50, 50), (255, 255, 255))
        self.empty_image = ImageTk.PhotoImage(image=empty_image)


        current_filename = tk.StringVar()

        invert_order = tk.BooleanVar()
        invert_order.set(True)
        segment_pages_individually = tk.BooleanVar()
        segment_pages_individually.set(True)

        selectionmode_var = tk.StringVar()
        selectionmode_var.set(SelectionMode.NO_ACTION)
        boxtype_var = tk.StringVar()
        boxtype_var.set(dataclasses.astuple(BoxProperty())[0])
        current_annotation_box_display_text = tk.StringVar()
        current_annotation_box_display_text.set("")
        current_annotation_type_length = tk.StringVar()
        current_annotation_type_length.set("")

        box_idx_to_image_dict = {}

        current_annotation_text = tk.StringVar()
        current_annotation_text.set("")
        current_annotation_suzipu_symbols = [tk.StringVar(), tk.StringVar()]
        current_annotation_suzipu_symbols[0].set(Symbol.NONE)
        current_annotation_suzipu_symbols[1].set(Symbol.NONE)

        current_box_is_excluded = tk.BooleanVar()
        current_box_is_excluded.set(False)

        current_box_is_line_break = tk.BooleanVar()
        current_box_is_line_break.set(False)

        mode_string = tk.StringVar()

        def construct_image():
            self.program_state.base_image_path = self.image_name_circle.get_current()
            self.images = []

            if self.number_of_pages.get() > 0:
                for idx in range(0, self.number_of_pages.get()):
                    image_name = self.image_name_circle.get_nth_from_current(idx)
                    self.images.append(cv2.cvtColor(cv2.imread(image_name), cv2.COLOR_BGR2RGB))

                max_width, max_height = 0, 0
                for image in self.images:
                    max_height = max(image.shape[0], max_height)
                    max_width = max(image.shape[1], max_width)

                for idx in range(len(self.images)):
                    self.images[idx] = cv2.copyMakeBorder(
                        src=self.images[idx],
                        top=0,
                        bottom=max_height - self.images[idx].shape[0],
                        left=0,
                        right=max_width - self.images[idx].shape[1],
                        borderType=cv2.BORDER_CONSTANT,
                        value=[255, 255, 255]
                    )

                if invert_order.get():
                    self.images.reverse()

                self.current_image = cv2.hconcat(self.images)
                current_filename.set(get_current_filename_from_circle(self.image_name_circle))
                self.must_be_changed = False

        def ensure_current_image():
            image_must_be_changed = self.must_be_changed or self.program_state.base_image_path is None
            if image_must_be_changed:
                construct_image()

        def handle_opencv_window():
            ensure_current_image()
            self.program_state.content, exit_flag = opencv_window.draw_and_handle_clicks(self.program_state,
                                                                                         selectionmode_var.get(),
                                                                                         boxtype_var.get(),
                                                                                         self.current_image,
                                                                                         get_current_annotation_index(),
                                                                                         set_current_annotation_index)

            if exit_flag:
                on_closing(main_window)()

        def must_be_changed():
            self.must_be_changed = True
            selectionmode_var.set(SelectionMode.NO_ACTION)  # to assure that before annotation the annotation button has to be clicked
            reset_annotation_vars()

        def on_new_segmentation():
            def shift_coordinates_by_width(coordinate_list, offset):
                l = []
                for element in coordinate_list:
                    l.append(((element[0][0] + offset, element[0][1]), (element[1][0] + offset, element[1][1])))
                return l
            self.program_state.content.reset()

            def wait(message):
                win = tk.Toplevel()
                win.title('Wait')
                new_label = tk.Label(win, text=message, padx=10, pady=10)
                new_label.pack()
                return win

            def segment():
                if segment_pages_individually.get():
                    current_width_offset = 0
                    boxes = []
                    for img in self.images:
                        current_box = predict_boxes(img, self.weights_path)
                        current_box = shift_coordinates_by_width(current_box, current_width_offset)
                        boxes += current_box
                        current_width_offset += img.shape[1]

                    self.program_state.content.create_from_coordinate_list(boxes)
                else:
                    self.program_state.content.create_from_coordinate_list(
                        predict_boxes(self.current_image, self.weights_path))

            segmentation_button.config(state="disabled")
            win = wait("Segmentation in progress. Please wait...")
            main_window.wait_visibility(win)
            win.update()
            segment()
            win.destroy()
            segmentation_button.config(state="normal")

        def on_infer_order():
            self.program_state.content.sort()
            create_sorted_segmentation_type_groups()

        def on_reset_segmentation():
            self.program_state.content.reset()
            must_be_changed()

        def on_previous():
            self.image_name_circle.previous()
            on_reset_segmentation()

        def on_next():
            self.image_name_circle.next()
            on_reset_segmentation()

        def create_sorted_segmentation_type_groups():
            annotation_cursor = {}
            for boxtype_var in dataclasses.astuple(BoxProperty()):
                try:
                    annotation_cursor[boxtype_var] = self.type_dict[boxtype_var].get_current()
                except KeyError:
                    annotation_cursor[boxtype_var] = None

                self.type_dict[boxtype_var] = []

            boxes = self.program_state.content
            for idx in range(len(boxes)):
                self.type_dict[boxes.get_index_type(idx)].append(idx)
                box_idx_to_image_dict[idx] = get_image_from_box_fixed_size(self.current_image, boxes.get_index_coordinates(idx))
            for boxtype_var in dataclasses.astuple(BoxProperty()):
                self.type_dict[boxtype_var] = ListCircle(self.type_dict[boxtype_var])

                if annotation_cursor[boxtype_var] is not None:
                    self.type_dict[boxtype_var].set_if_present(
                        annotation_cursor[boxtype_var])  # restore previous state if possible

        def on_click_annotate():
            create_sorted_segmentation_type_groups()
            set_annotation_properties()

        def get_current_annotation_index():
            try:
                if selectionmode_var.get() == SelectionMode.ANNOTATE:
                    return access_current_segmentation_cycle().get_current()
                return None
            except Exception:
                return None

        def set_current_annotation_index(idx: int):
            try:
                box_type = self.program_state.content.get_index_type(idx)
                boxtype_var.set(box_type)
                local_idx = self.type_dict[box_type].list.index(idx)
                access_current_segmentation_cycle().set_to_index(local_idx)
                set_annotation_properties()
                on_activate_deactivate_annotation_frame()
                annotation_frame.update_musical_image_display()
            except Exception as e:
                print(e)

        def set_annotation_properties():
            current_idx = get_current_annotation_index()

            def set_annotation_image():
                try:
                    if len(access_current_segmentation_cycle()):
                        annotation_frame.set_image(box_idx_to_image_dict[current_idx])
                        current_annotation_box_display_text.set(
                            f"{access_current_segmentation_cycle().current_position + 1} / {len(access_current_segmentation_cycle())}")
                        current_annotation_type_length.set(f"{len(access_current_segmentation_cycle())}")
                except KeyError as e:
                    print(f"Could not retrieve image with index {current_idx}. {e}")

            def set_annotation_variables():
                current_box_annotation = self.program_state.content.get_index_annotation(current_idx)

                # very important! we must load the box excludedness first, because the change of current_annotation_text
                # triggers the saving routine!
                current_box_is_excluded.set(self.program_state.content.is_index_excluded(current_idx))
                current_box_is_line_break.set(self.program_state.content.is_index_line_break(current_idx))

                if boxtype_var.get() == BoxProperty.MUSIC:
                    try:
                        current_annotation_suzipu_symbols[0].set(current_box_annotation[0])
                    except IndexError:
                        current_annotation_suzipu_symbols[0].set(Symbol.NONE)
                    try:
                        current_annotation_suzipu_symbols[1].set(current_box_annotation[1])
                    except IndexError:
                        current_annotation_suzipu_symbols[1].set(Symbol.NONE)
                    current_annotation_text.set("")
                else:
                    current_annotation_suzipu_symbols[0].set(Symbol.NONE)
                    current_annotation_suzipu_symbols[1].set(Symbol.NONE)
                    current_annotation_text.set(current_box_annotation)

            if current_idx is not None:
                set_annotation_image()
                set_annotation_variables()

        def access_current_segmentation_cycle() -> ListCircle:
            return self.type_dict[boxtype_var.get()]

        def on_annotate_previous():
            access_current_segmentation_cycle().previous()
            set_annotation_properties()

        def on_save_annotation_to_box(*args):
            idx = get_current_annotation_index()

            def character_limit():
                if len(current_annotation_text.get()) > 0:
                    current_annotation_text.set(current_annotation_text.get()[0:1])

            character_limit()

            annotation_string = ""
            if selectionmode_var.get() == SelectionMode.ANNOTATE:
                if boxtype_var.get() == BoxProperty.MUSIC:
                    first_symbol = current_annotation_suzipu_symbols[0].get()
                    if first_symbol == Symbol.NONE:
                        annotation_string = ""
                    else:
                        annotation_string = first_symbol
                        second_symbol = current_annotation_suzipu_symbols[1].get()
                        if second_symbol != Symbol.NONE:
                            annotation_string += second_symbol
                else:
                    annotation_string = current_annotation_text.get()

                self.program_state.content.set_index_annotation(get_current_annotation_index(), annotation_string)
                self.program_state.content.set_index_excluded(get_current_annotation_index(), current_box_is_excluded.get())
                self.program_state.content.set_index_line_break(get_current_annotation_index(), current_box_is_line_break.get())

        def on_fill_all_boxes_of_type(text: str):
            if selectionmode_var.get() == SelectionMode.ANNOTATE:
                if boxtype_var.get() == BoxProperty.MUSIC:
                    for idx, box_index in enumerate(self.type_dict[boxtype_var.get()].list):
                        suzipu_list = text.replace(" ", "").split("|")
                        self.program_state.content.set_index_annotation(box_index, suzipu_list[idx])
                else:
                    for idx, box_index in enumerate(self.type_dict[boxtype_var.get()].list):
                        self.program_state.content.set_index_annotation(box_index, text[idx])

        def on_annotate_next():
            access_current_segmentation_cycle().next()
            set_annotation_properties()

        def on_save_image():
            draw_image = opencv_window.get_current_draw_image()
            if draw_image is not None:
                file_path = asksaveasfilename(
                    initialdir=self.output_dir,
                    initialfile=get_current_filename_from_circle(self.image_name_circle),
                    defaultextension=".png",
                    filetypes=[("All Files", "*.*"), ("JPEG File", "*.jpg"), ("PNG File", "*.png")])
                if file_path:
                    cv2.imwrite(file_path, draw_image)

        invalid_mode_image = open_file_as_tk_image(INVALID_MODE_IMAGE)
        go_into_annotation_mode_image = open_file_as_tk_image(GO_INTO_ANNOTATION_MODE_IMAGE)

        def get_content_list(key: str):
            try:
                return [self.program_state.content.get_index_annotation(box_idx) for box_idx in
                        self.type_dict[key].list]
            except AttributeError:
                return None

        def get_box_images(key: str):
            try:
                coordinates = [self.program_state.content.get_index_coordinates(box_idx) for box_idx in self.type_dict[key].list]
                images = [get_image_from_box_ai_assistant(self.current_image, coord) for coord in coordinates]
                return images
            except AttributeError:
                return None

        def get_mode_string():
            string = ""
            for character in get_content_list(BoxProperty.MODE):
                string += character
            return string

        def get_line_break_indices(key):
            raw_indices = self.program_state.content.get_line_break_indices()
            box_idx_list = self.type_dict[key].list
            line_break_idxs = []
            for enumeration_idx, box_idx in enumerate(box_idx_list):
                if box_idx in raw_indices:
                    line_break_idxs.append(enumeration_idx)
            return line_break_idxs

        def get_notation_image():
            if selectionmode_var.get() != SelectionMode.ANNOTATE:
                return None

            try:
                music_list = get_content_list(BoxProperty.MUSIC)
                lyrics_list = get_content_list(BoxProperty.LYRICS)
                line_break_idxs = get_line_break_indices(BoxProperty.LYRICS)
            except KeyError:
                return None

            mode = GongdiaoModeList.from_string(mode_string.get())

            try:
                music_list = mode.convert_pitches_in_list(music_list)
            except TypeError:  # This happens when the chosen mode dows not match the piece
                return None

            fingering = display_notes_frame.get_transposition()

            if display_notes_frame.is_jianpu():
                notation_img = notation_to_jianpu(self.notation_resources.small_font,
                                                  self.notation_resources.jianpu_image_dict,
                                                  music_list, lyrics_list,
                                                  line_break_idxs,
                                                  fingering)
            else:
                notation_img = notation_to_western(self.notation_resources.small_font,
                                                   self.notation_resources.western_image_dict,
                                                   music_list, lyrics_list,
                                                   line_break_idxs,
                                                   fingering)

            return notation_img

        def get_complete_notation_image():
            def get_content_list(key: str):
                return [self.program_state.content.get_index_annotation(box_idx) for box_idx in
                        self.type_dict[key].list]

            def get_content_string(key: str):
                string = ""
                line_break_indices = get_line_break_indices(key)
                for idx, character in enumerate(get_content_list(key)):
                    string += character

                    if key == BoxProperty.TITLE or key == BoxProperty.PREFACE:  # no breaks are needed for the mode:
                        if idx in line_break_indices:
                            string += "\n"
                return string

            notation_img = get_notation_image()
            metadata_img = construct_metadata_image(self.notation_resources.title_font,
                                                    self.notation_resources.small_font,
                                                    get_content_string(BoxProperty.TITLE),
                                                    f"{get_content_string(BoxProperty.MODE)}（{GongdiaoModeList.from_string(mode_string.get()).chinese_name}）",
                                                    get_content_string(BoxProperty.PREFACE),
                                                    image_width=notation_img.width)
            combined_img = vertical_composition([metadata_img, notation_img])
            combined_img = add_border(combined_img, 150, 200)
            return combined_img

        def save_to_musicxml(file_path):
            def get_content_list(key: str):
                return [self.program_state.content.get_index_annotation(box_idx) for box_idx in
                        self.type_dict[key].list]

            def get_content_string(key: str):
                string = ""
                line_break_indices = get_line_break_indices(key)
                for idx, character in enumerate(get_content_list(key)):
                    string += character

                    if key == BoxProperty.TITLE or key == BoxProperty.PREFACE:  # no breaks are needed for the mode:
                        if idx in line_break_indices:
                            string += "\n"
                return string

            try:
                music_list = get_content_list(BoxProperty.MUSIC)
                lyrics_list = get_content_list(BoxProperty.LYRICS)
                line_break_idxs = get_line_break_indices(BoxProperty.LYRICS)
            except KeyError:
                return None

            mode = GongdiaoModeList.from_string(mode_string.get())

            try:
                music_list = mode.convert_pitches_in_list(music_list)
            except TypeError:  # This happens when the chosen mode dows not match the piece
                return None

            fingering = display_notes_frame.get_transposition()

            title = get_content_string(BoxProperty.TITLE)
            mode_str = f"{get_content_string(BoxProperty.MODE)}（{GongdiaoModeList.from_string(mode_string.get()).chinese_name}）"
            preface = get_content_string(BoxProperty.PREFACE)

            write_to_musicxml(file_path, music_list, lyrics_list, fingering, title, mode_str, preface)

            return None

        def on_save_notation():
            main_window.focus_force()
            draw_image = opencv_window.get_current_draw_image()
            if draw_image is not None:
                file_path = asksaveasfilename(
                    initialdir=self.output_dir,
                    initialfile=self.initial_filename,
                    defaultextension=".png",
                    filetypes=[("PNG File", "*.png"), ("All Files", "*.*")])
                if file_path:
                    complete_notation_image = get_complete_notation_image()
                    complete_notation_image.save(file_path)

        def on_save_musicxml():
            main_window.focus_force()
            draw_image = opencv_window.get_current_draw_image()
            if draw_image is not None:
                file_path = asksaveasfilename(
                    initialdir=self.output_dir,
                    initialfile=self.initial_filename,
                    defaultextension=".musicxml",
                    filetypes=[("MusicXML File", "*.musicxml"), ("All Files", "*.*")])
                if file_path:
                    save_to_musicxml(file_path)

        def on_save():
            self.program_state.number_of_pages = self.number_of_pages.get()

            self.program_state.mode_properties = annotation_frame.get_mode_properties()
            new_program_state = copy.copy(self.program_state)

            try:
                json_state = state_to_json(new_program_state)
            except AssertionError as e:
                showerror("Error", message=str(e))
                return

            file_path = asksaveasfilename(
                initialdir=self.output_dir,
                initialfile=self.initial_filename,
                defaultextension=".json",
                filetypes=[("JSON file", "*.json"), ("All files", "*.*")])
            if file_path:
                with open(file_path, "w") as json_file:
                    image_list = []
                    for idx in range(json_state["number_of_pages"]):
                        image_list.append(os.path.relpath(self.image_name_circle.get_nth_from_current(idx), start=os.path.dirname(file_path)))  # we must save the relative path without modifying the program state

                    del json_state["base_image_path"]
                    del json_state["number_of_pages"]
                    json_state["images"] = image_list

                    json.dump(json_state, json_file)

        def on_save_text():
            file_path = asksaveasfilename(
                initialdir=self.output_dir,
                initialfile=self.initial_filename,
                defaultextension=".txt",
                filetypes=[("Text file", "*.txt"), ("All files", "*.*")])
            if file_path:
                def get_content_string(key):
                    create_sorted_segmentation_type_groups()
                    try:
                        raw_content_list = [self.program_state.content.get_index_annotation(box_idx) for box_idx in self.type_dict[key].list]

                        content_string = ""
                        for string in raw_content_list:
                            if string == "":  # if empty box, display as blank
                                string = " "
                            content_string += string
                            if key == BoxProperty.MUSIC:
                                content_string += "|"
                        if key == BoxProperty.MUSIC:
                            return content_string[0:-1]  #remove the last '|'
                        return content_string
                    except KeyError:
                        return ""

                with open(file_path, "w") as text_file:
                    text_file.write(
                        f"Title: {get_content_string(BoxProperty.TITLE)}\n\n"
                        f"Mode: {get_content_string(BoxProperty.MODE)}（{GongdiaoModeList.from_string(mode_string.get()).chinese_name}）\n\n"
                        f"Preface: {get_content_string(BoxProperty.PREFACE)}\n\n"
                        f"Lyrics: {get_content_string(BoxProperty.LYRICS)}\n\n"
                        f"Music: {get_content_string(BoxProperty.MUSIC)}\n\n"
                    )

        def on_new():
            images_dir = filedialog.askdirectory(
                title='Open the image directory (must contain image files)',
                initialdir=self.output_dir,
                mustexist=True
            )

            if len(get_folder_contents(images_dir, only_images=True)) == 0:  # no images in folder!
                showerror("Error",
                          "The selected directory does not contain any image files (PNG, TIFF, JPEG)! Abort.")
            else:
                self.images_dir = images_dir
                self.output_dir = images_dir
                self.initial_filename = "untitled"
                self.initialize(program_state)
                right_increment_decrement_widget.set_counter(self.number_of_pages.get())
                mode_string.set(GongdiaoModeList.from_properties(self.program_state.mode_properties).name)

                annotation_frame.set_mode_properties(self.program_state.mode_properties)

                self.image_name_circle.set_if_present(os.path.join(self.images_dir, Path(program_state.base_image_path).name))
                must_be_changed()
                on_activate_deactivate_annotation_frame()

        def on_load():
            filetypes = (
                ('JSON file', '*.json'),
                ('All files', '*.*')
            )
            file_path = filedialog.askopenfilename(
                title='Open JSON file',
                initialdir=self.output_dir,
                filetypes=filetypes
            )

            if file_path:
                with open(file_path, "r") as json_file:
                    json_contents = json.load(json_file)
                    program_state = ProgramState.load(json_contents)
                    self.images_dir = os.path.join(os.path.dirname(file_path), os.path.dirname(program_state.base_image_path))
                    self.output_dir = os.path.dirname(file_path)
                    self.initial_filename = Path(file_path).stem
                    self.initialize(program_state)
                    right_increment_decrement_widget.set_counter(self.number_of_pages.get())
                    mode_string.set(GongdiaoModeList.from_properties(self.program_state.mode_properties).name)

                    annotation_frame.set_mode_properties(self.program_state.mode_properties)

                    self.image_name_circle.set_if_present(os.path.join(self.images_dir, Path(program_state.base_image_path).name))
                    must_be_changed()
                    on_activate_deactivate_annotation_frame()

        prev_next_increment_frame = tk.Frame(main_window)
        increment_decrement_subframe = tk.LabelFrame(prev_next_increment_frame, text="Number of pages")
        previous_next = PreviousNextFrame(prev_next_increment_frame, current_filename, on_previous, on_next).get_frame()
        right_increment_decrement_widget = IncrementDecrementFrame(increment_decrement_subframe, self.number_of_pages, must_be_changed)
        right_increment_decrement = right_increment_decrement_widget.get_frame()
        previous_next.grid(row=0, column=0)

        right_increment_decrement.pack(pady=10)
        increment_decrement_subframe.grid(row=0, column=1)

        segmentation_frame = tk.LabelFrame(main_window, text="Segmentation and Order")
        inner_frame = tk.Frame(segmentation_frame)
        #invert_order_checkbutton = tk.Checkbutton(checkbox_options_frame, text='Invert order', variable=invert_order,
        #                                          onvalue=1, offvalue=0, command=must_be_changed)
        segment_pages_individually_checkbutton = tk.Checkbutton(inner_frame, text='Segment individually',
                                                                variable=segment_pages_individually, onvalue=1,
                                                                offvalue=0, command=must_be_changed)
        segmentation_button = tk.Button(inner_frame, text="New Segmentation", command=on_new_segmentation)
        infer_order_button = tk.Button(inner_frame, text="Infer Box Order and Column Breaks", command=on_infer_order)
        segmentation_button.grid(row=0, column=0)
        infer_order_button.grid(row=0, column=1)
        segment_pages_individually_checkbutton.grid(row=1, column=0)
        inner_frame.pack(padx=10, pady=10)

        save_load_buttons = SaveLoadFrame(main_window, on_save_image, on_new, on_save, on_save_text, on_load).get_frame()
        annotation_frame = AnnotationFrame(main_window, boxtype_var,
                                           current_annotation_box_display_text, current_annotation_type_length,
                                           current_annotation_text,
                                           current_annotation_suzipu_symbols,
                                           current_box_is_excluded,
                                           current_box_is_line_break,
                                           on_annotate_previous, on_annotate_next, on_save_annotation_to_box,
                                           on_fill_all_boxes_of_type,
                                           get_box_images,
                                           mode_variable=mode_string,
                                           get_mode_string=get_mode_string)
        current_annotation_text.trace("w", on_save_annotation_to_box)

        notation_window = tk.Toplevel()
        notation_window.title("Suzipu Musical Annotation Tool - Additional Info")
        notation_window.protocol("WM_DELETE_WINDOW", lambda: None)
        notation_window.resizable(False, False)
        #display_notes_frame = AdditionalInfoFrame(notation_window, mode_string, on_save_notation, on_save_musicxml, get_mode_string)
        display_notes_frame = DisplayNotesFrame(notation_window, on_save_notation=on_save_notation, on_save_musicxml=on_save_musicxml)

        def reset_annotation_vars():
            current_annotation_text.set("")
            current_annotation_suzipu_symbols[0].set(Symbol.NONE)
            current_annotation_suzipu_symbols[1].set(Symbol.NONE)
            current_annotation_box_display_text.set(None)
            current_annotation_type_length.set(None)
            current_box_is_excluded.set(False)
            current_box_is_line_break.set(False)
            annotation_frame.set_image(None)

        def handle_additional_info():
            def resize_to_width(pil_image):
                height, width = pil_image.height, pil_image.width
                #if width > 600:
                #    new_width = 600
                #    new_height = int(new_width * height / width)
                #    pil_image = pil_image.resize((new_width, new_height))
                #elif height > 600:
                #    new_height = 600
                #    new_width = int(new_height * width / height)
                #    pil_image = pil_image.resize((new_width, new_height))
                percentage = 0.5
                pil_image = pil_image.resize((int(width*percentage), int(height*percentage)))
                return pil_image

            notation_img = get_notation_image()

            if notation_img:
                notation_img = resize_to_width(notation_img)
                notation_img = ImageTk.PhotoImage(image=notation_img)
                display_notes_frame.set_image(notation_img)
            else:
                display_notes_frame.set_image(invalid_mode_image)

            def get_suzipu_list():
                try:
                    suzipu_list = [self.program_state.content.get_index_annotation(box_idx) for box_idx in
                                   self.type_dict[BoxProperty.MUSIC].list]

                    single_list = []
                    for suzipu in suzipu_list:
                        for char in suzipu:
                            single_list.append(char)

                    from collections import Counter
                    cntr = dict(Counter(single_list))
                    return cntr

                except AttributeError:
                    return None

            if selectionmode_var.get() == SelectionMode.ANNOTATE:
                display_notes_frame.set_state(True)
                # TODO: Restructure
                #display_notes_frame.set_statistics(get_suzipu_list())
            else:
                display_notes_frame.set_state(False)
                display_notes_frame.set_image(go_into_annotation_mode_image)

        def start_opencv_timer():
            handle_opencv_window()
            main_window.after(1, start_opencv_timer)

        def start_notation_window_timer():
            handle_additional_info()
            main_window.after(100, start_notation_window_timer)

        def on_activate_deactivate_annotation_frame():
            state = selectionmode_var.get() == SelectionMode.ANNOTATE and selection_buttons.is_active and len(self.type_dict[boxtype_var.get()].list) > 0

            annotation_frame.set_state(state)

            if not state:
                annotation_frame.set_image(self.empty_image)

        selection_buttons = SelectionFrame(main_window, selectionmode_var, boxtype_var, on_click_annotate,
                                           lambda: [on_activate_deactivate_annotation_frame(), annotation_frame.update_musical_image_display()],
                                           lambda: [set_annotation_properties(), on_activate_deactivate_annotation_frame(), annotation_frame.update_musical_image_display()])

        save_load_buttons.grid(row=0, column=1, pady=10)

        prev_next_increment_frame.grid(row=1, column=1, padx=10, pady=10)

        segmentation_frame.grid(row=2, column=1, pady=10)
        selection_buttons.get_frame().grid(row=4, column=1, pady=10)
        annotation_frame.get_frame().grid(row=5, column=1, padx=10, pady=10)

        display_notes_frame.get_frame().grid(row=6, column=1)

        main_window.after(1, start_opencv_timer)
        main_window.after(1, start_notation_window_timer)

        def _on_closing():
            on_closing(main_window)()

        main_window.protocol("WM_DELETE_WINDOW", _on_closing)

        annotation_frame.set_image(self.empty_image)

        main_window.mainloop()

if __name__ == "__main__":
    program_state = ProgramState()

    weights_path = "./weights/HRCenterNet.pth.tar"

    if not os.path.isfile(weights_path):
        showerror("Error", "'HRCenterNet.pth.tar' could not be found. Please download the file 'HRCenterNet.pth.tar' and put it into the folder 'weights'. Abort.")
        exit(-1)

    main_window = MainWindow(program_state, weights_path)
    main_window.exec()
