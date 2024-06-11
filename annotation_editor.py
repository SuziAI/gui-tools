import copy
import dataclasses
import importlib
import json

from pathlib import Path

import cv2
import os

import tkinter as tk
from tkinter import filedialog
from tkinter.filedialog import asksaveasfilename
from tkinter.messagebox import showerror

from PIL import ImageTk

from src.auxiliary import is_point_in_rectangle, Colors, \
    box_property_to_color, get_image_from_box_fixed_size, open_file_as_tk_image, \
    is_rectangle_big_enough, \
    state_to_json, get_folder_contents, BoxType, BoxesWithType, ListCycle, \
    BoxManipulationAction, draw_transparent_rectangle, draw_transparent_line
from src.programstate import PieceProperties, GuiState, ProgramState
from src.config import GO_INTO_ANNOTATION_MODE_IMAGE, INVALID_MODE_IMAGE, PLUGIN_NOT_SUPPORT_NOTATION_IMAGE
from src.widgets_auxiliary import on_closing, IncrementDecrementFrame, PreviousNextFrame, \
    SelectionFrame, SaveLoadFrame, PiecePropertiesFrame
from src.widgets_annotation import AnnotationFrame
from src.plugins.suzipu_lvlvpu_gongchepu.common import GongdiaoModeList, DisplayNotesFrame
from src.plugins.suzipu_lvlvpu_gongchepu.notes_to_image import common_notation_to_jianpu, common_notation_to_staff, construct_metadata_image, vertical_composition, add_border, write_to_musicxml


class MainWindow:
    def __init__(self, weights_path: str):
        self.main_window = tk.Tk()
        self.main_window.title("Chinese Musical Annotation Tool- Main Window")

        self.program_state = ProgramState(piece_properties=PieceProperties(), gui_state=GuiState(self.main_window, weights_path))

    def exec(self):
        opencv_window = OpenCvWindow("Chinese Musical Annotation Tool - Canvas", self.program_state)

        def ensure_current_image():
            image_must_be_changed = self.program_state.gui_state.must_be_changed or self.program_state.piece_properties.base_image_path is None
            if image_must_be_changed:
                self.program_state.construct_image()

        def handle_opencv_window():
            ensure_current_image()
            self.program_state.piece_properties.content, exit_flag = opencv_window.draw_and_handle_clicks(self.program_state.piece_properties,
                                                                                                          self.program_state.gui_state.tk_current_action.get(),
                                                                                                          self.program_state.gui_state.tk_current_boxtype.get(),
                                                                                                          self.program_state.gui_state.current_image,
                                                                                                          self.program_state.get_current_annotation_index(),
                                                                                                          set_current_annotation_index)

            if exit_flag:
                on_closing(main_window)()

        def must_be_changed():
            self.program_state.gui_state.must_be_changed = True
            self.program_state.gui_state.tk_current_action.set(BoxManipulationAction.NO_ACTION)  # to assure that before annotation the annotation button has to be clicked
            reset_annotation_vars()

        def on_infer_order():
            self.program_state.piece_properties.content.sort()
            create_sorted_segmentation_type_groups()

        def on_min_bounding_rect():
            self.program_state.piece_properties.content.fit_min_bounding_rects(self.program_state.gui_state.current_image)

        def on_reset_segmentation():
            self.program_state.piece_properties.content.reset()
            must_be_changed()

        def on_previous():
            self.program_state.gui_state.image_name_circle.previous()
            on_reset_segmentation()

        def on_next():
            self.program_state.gui_state.image_name_circle.next()
            on_reset_segmentation()

        def create_sorted_segmentation_type_groups():
            annotation_cursor = {}
            for boxtype_var in dataclasses.astuple(BoxType()):
                try:
                    annotation_cursor[boxtype_var] = self.program_state.gui_state.type_to_cycle_dict[boxtype_var].get_current()
                except KeyError:
                    annotation_cursor[boxtype_var] = None

                self.program_state.gui_state.type_to_cycle_dict[boxtype_var] = []

            boxes = self.program_state.piece_properties.content
            for idx in range(len(boxes)):
                self.program_state.gui_state.type_to_cycle_dict[boxes.get_index_type(idx)].append(idx)
                self.program_state.gui_state.box_idx_to_tkinter_image_dict[idx] = get_image_from_box_fixed_size(self.program_state.gui_state.current_image, boxes.get_index_coordinates(idx))
            for boxtype_var in dataclasses.astuple(BoxType()):
                self.program_state.gui_state.type_to_cycle_dict[boxtype_var] = ListCycle(self.program_state.gui_state.type_to_cycle_dict[boxtype_var])

                if annotation_cursor[boxtype_var] is not None:
                    self.program_state.gui_state.type_to_cycle_dict[boxtype_var].set_if_present(
                        annotation_cursor[boxtype_var])  # restore previous state if possible

        def on_click_annotate():
            create_sorted_segmentation_type_groups()
            self.program_state.update_annotation_image_and_variables()

        def set_current_annotation_index(idx: int):
            try:
                box_type = self.program_state.piece_properties.content.get_index_type(idx)
                self.program_state.gui_state.tk_current_boxtype.set(box_type)
                local_idx = self.program_state.gui_state.type_to_cycle_dict[box_type].list.index(idx)
                self.program_state.get_current_type_cycle().set_to_index(local_idx)
                self.program_state.update_annotation_image_and_variables()
                on_activate_deactivate_annotation_frame()
                annotation_frame.update_annotation()
            except Exception as e:
                print(e)

        def on_save_image():
            draw_image = opencv_window.get_current_draw_image()
            if draw_image is not None:
                file_path = asksaveasfilename(
                    initialdir=self.program_state.gui_state.output_dir,
                    initialfile=self.program_state.get_first_page_image_name(),
                    defaultextension=".png",
                    filetypes=[("All Files", "*.*"), ("JPEG File", "*.jpg"), ("PNG File", "*.png")])
                if file_path:
                    cv2.imwrite(file_path, draw_image)

        invalid_mode_image = open_file_as_tk_image(INVALID_MODE_IMAGE)
        go_into_annotation_mode_image = open_file_as_tk_image(GO_INTO_ANNOTATION_MODE_IMAGE)
        plugin_not_support_notation_image = open_file_as_tk_image(PLUGIN_NOT_SUPPORT_NOTATION_IMAGE)

        def get_content_list(key: str):
            try:
                return [self.program_state.piece_properties.content.get_index_annotation(box_idx) for box_idx in
                        self.program_state.gui_state.type_to_cycle_dict[key].list]
            except AttributeError:
                return None

        def get_line_break_indices(key):
            raw_indices = self.program_state.piece_properties.content.get_line_break_indices()
            box_idx_list = self.program_state.gui_state.type_to_cycle_dict[key].list
            line_break_idxs = []
            for enumeration_idx, box_idx in enumerate(box_idx_list):
                if box_idx in raw_indices:
                    line_break_idxs.append(enumeration_idx)
            return line_break_idxs

        def get_notation_image():
            if self.program_state.gui_state.tk_current_action.get() != BoxManipulationAction.ANNOTATE:
                return None

            try:
                music_list = get_content_list(BoxType.MUSIC)
                lyrics_list = get_content_list(BoxType.LYRICS)
                line_break_idxs = get_line_break_indices(BoxType.LYRICS)
            except KeyError:
                return None

            mode = GongdiaoModeList.from_string(self.program_state.gui_state.tk_current_mode_string.get())

            fingering = display_notes_frame.get_transposition()

            plugin_name = self.program_state.gui_state.tk_notation_plugin_selection.get().lower()
            module = importlib.import_module(f"src.plugins.{plugin_name}")

            try:
                if display_notes_frame.is_jianpu():
                    notation_img = module.notation_to_jianpu(mode,
                                                          music_list, lyrics_list,
                                                          line_break_idxs,
                                                          fingering)
                else:
                    notation_img = module.notation_to_staff(mode,
                                                           music_list, lyrics_list,
                                                           line_break_idxs,
                                                           fingering)
            except NotImplementedError:
                return None

            return notation_img

        def get_complete_notation_image():
            def get_content_list(key: str):
                return [self.program_state.piece_properties.content.get_index_annotation(box_idx) for box_idx in
                        self.program_state.gui_state.type_to_cycle_dict[key].list]

            def get_content_string(key: str):
                string = ""
                line_break_indices = get_line_break_indices(key)
                for idx, character in enumerate(get_content_list(key)):
                    string += character

                    if key == BoxType.TITLE or key == BoxType.PREFACE:  # no breaks are needed for the mode:
                        if idx in line_break_indices:
                            string += "\n"
                return string

            notation_img = get_notation_image()
            metadata_img = construct_metadata_image(self.program_state.gui_state.notation_resources.title_font,
                                                    self.program_state.gui_state.notation_resources.small_font,
                                                    get_content_string(BoxType.TITLE),
                                                    f"{get_content_string(BoxType.MODE)}（{GongdiaoModeList.from_string(self.program_state.gui_state.tk_current_mode_string.get()).chinese_name}）",
                                                    get_content_string(BoxType.PREFACE),
                                                    image_width=notation_img.width)
            combined_img = vertical_composition([metadata_img, notation_img])
            combined_img = add_border(combined_img, 150, 200)
            return combined_img

        def save_to_musicxml(file_path):
            def get_content_list(key: str):
                return [self.program_state.piece_properties.content.get_index_annotation(box_idx) for box_idx in
                        self.program_state.gui_state.type_to_cycle_dict[key].list]

            def get_content_string(key: str):
                string = ""
                line_break_indices = get_line_break_indices(key)
                for idx, character in enumerate(get_content_list(key)):
                    string += character

                    if key == BoxType.TITLE or key == BoxType.PREFACE:  # no breaks are needed for the mode:
                        if idx in line_break_indices:
                            string += "\n"
                return string

            try:
                music_list = get_content_list(BoxType.MUSIC)
                lyrics_list = get_content_list(BoxType.LYRICS)
                line_break_idxs = get_line_break_indices(BoxType.LYRICS)
            except KeyError:
                return None

            mode = GongdiaoModeList.from_string(self.program_state.gui_state.tk_current_mode_string.get())

            try:
                music_list = mode.convert_pitches_in_list(music_list)
            except TypeError:  # This happens when the chosen mode dows not match the piece
                return None

            fingering = display_notes_frame.get_transposition()

            title = get_content_string(BoxType.TITLE)
            mode_str = f"{get_content_string(BoxType.MODE)}（{GongdiaoModeList.from_string(self.program_state.gui_state.tk_current_mode_string.get()).chinese_name}）"
            preface = get_content_string(BoxType.PREFACE)

            write_to_musicxml(file_path, music_list, lyrics_list, fingering, title, mode_str, preface)

            return None

        def on_save_notation():
            self.main_window.focus_force()
            draw_image = opencv_window.get_current_draw_image()
            if draw_image is not None:
                file_path = asksaveasfilename(
                    initialdir=self.program_state.gui_state.output_dir,
                    initialfile=self.program_state.gui_state.initial_filename,
                    defaultextension=".png",
                    filetypes=[("PNG File", "*.png"), ("All Files", "*.*")])
                if file_path:
                    complete_notation_image = get_complete_notation_image()
                    complete_notation_image.save(file_path)

        def on_save_musicxml():
            self.main_window.focus_force()
            draw_image = opencv_window.get_current_draw_image()
            if draw_image is not None:
                file_path = asksaveasfilename(
                    initialdir=self.program_state.gui_state.output_dir,
                    initialfile=self.program_state.gui_state.initial_filename,
                    defaultextension=".musicxml",
                    filetypes=[("MusicXML File", "*.musicxml"), ("All Files", "*.*")])
                if file_path:
                    save_to_musicxml(file_path)

        def on_save():
            self.program_state.piece_properties.number_of_pages = self.program_state.gui_state.number_of_pages.get()

            self.program_state.piece_properties.mode_properties = annotation_frame.get_mode_properties()
            self.program_state.piece_properties.composer = self.program_state.gui_state.tk_current_composer.get()
            self.program_state.piece_properties.notation_type = self.program_state.gui_state.tk_notation_plugin_selection.get()
            new_program_state = copy.copy(self.program_state.piece_properties)

            try:
                json_state = state_to_json(new_program_state, self.program_state.gui_state)
            except AssertionError as e:
                showerror("Error", message=str(e))
                return

            file_path = asksaveasfilename(
                initialdir=self.program_state.gui_state.output_dir,
                initialfile=self.program_state.gui_state.initial_filename,
                defaultextension=".json",
                filetypes=[("JSON file", "*.json"), ("All files", "*.*")])
            if file_path:
                with open(file_path, "w") as json_file:
                    image_list = []
                    for idx in range(self.program_state.gui_state.number_of_pages.get()):
                        image_list.append(os.path.relpath(self.program_state.gui_state.image_name_circle.get_nth_from_current(idx), start=os.path.dirname(file_path)))  # we must save the relative path without modifying the program state

                    json_state["images"] = image_list
                    keyorder = ['version', 'notation_type', 'composer', 'mode_properties', 'images', 'content']
                    json_state = {k: json_state[k] for k in keyorder if k in json_state}

                    self.program_state.gui_state.initial_filename = Path(file_path).stem
                    json.dump(json_state, json_file)

        def on_save_text():
            file_path = asksaveasfilename(
                initialdir=self.program_state.gui_state.output_dir,
                initialfile=self.program_state.gui_state.initial_filename,
                defaultextension=".txt",
                filetypes=[("Text file", "*.txt"), ("All files", "*.*")])
            if file_path:
                def get_content_string(key):
                    create_sorted_segmentation_type_groups()
                    try:
                        raw_content_list = [
                            self.program_state.piece_properties.content.get_index_annotation(box_idx) for box_idx in
                            self.program_state.gui_state.type_to_cycle_dict[key].list]

                        if key == BoxType.MUSIC:
                            return json.dumps(raw_content_list)
                        else:
                            content_string = ""
                            for string in raw_content_list:
                                if string == "":  # if empty box, display as blank
                                    string = " "
                                content_string += string
                                if key == BoxType.MUSIC:
                                    content_string += "|"
                            if key == BoxType.MUSIC:
                                return content_string[0:-1]  # remove the last '|'
                            return content_string
                    except KeyError:
                        return ""

                with open(file_path, "w") as text_file:
                    text_file.write(
                        f"Title: {get_content_string(BoxType.TITLE)}\n\n"
                        f"Mode: {get_content_string(BoxType.MODE)}（{GongdiaoModeList.from_string(self.program_state.gui_state.tk_current_mode_string.get()).chinese_name}）\n\n"
                        f"Preface: {get_content_string(BoxType.PREFACE)}\n\n"
                        f"Lyrics: {get_content_string(BoxType.LYRICS)}\n\n"
                        f"Music: {get_content_string(BoxType.MUSIC)}\n\n"
                        f"Lyrics (ind.): {get_content_string(BoxType.LYRICS_IND)}\n\n"
                        f"Music (ind.): {get_content_string(BoxType.MUSIC_IND)}\n\n"
                        f"Unmarked: {get_content_string(BoxType.UNMARKED)}\n\n"
                    )

        def on_new():
            images_dir = filedialog.askdirectory(
                title='Open the image directory (must contain image files)',
                initialdir=self.program_state.gui_state.output_dir,
                mustexist=True
            )

            if not images_dir:
                pass
            elif len(get_folder_contents(images_dir, only_images=True)) == 0:  # no images in folder!
                showerror("Error",
                          "The selected directory does not contain any image files (PNG, TIFF, JPEG)! Abort.")
            else:
                self.program_state.gui_state.images_dir = images_dir
                self.program_state.gui_state.output_dir = images_dir
                self.program_state.gui_state.initial_filename = "untitled"
                self.program_state.initialize_from_piece_properties(PieceProperties())
                right_increment_decrement_widget.set_counter(self.program_state.gui_state.number_of_pages.get())
                self.program_state.gui_state.tk_current_mode_string.set(GongdiaoModeList.from_properties(self.program_state.piece_properties.mode_properties).name)

                annotation_frame.set_mode_properties(self.program_state.piece_properties.mode_properties)
                path = None
                try:
                    path = os.path.join(self.program_state.gui_state.images_dir, Path(self.program_state.piece_properties.base_image_path).name)
                except TypeError:
                    pass
                self.program_state.gui_state.image_name_circle.set_if_present(path)
                must_be_changed()
                on_activate_deactivate_annotation_frame()
                on_reset_segmentation()

        def on_load():
            filetypes = (
                ('JSON file', '*.json'),
                ('All files', '*.*')
            )
            file_path = filedialog.askopenfilename(
                title='Open JSON file',
                initialdir=self.program_state.gui_state.output_dir,
                filetypes=filetypes
            )

            if file_path:
                with open(file_path, "r") as json_file:
                    json_contents = json.load(json_file)
                    piece_properties = PieceProperties.load(json_contents)
                    self.program_state.gui_state.images_dir = os.path.join(os.path.dirname(file_path), os.path.dirname(piece_properties.base_image_path))
                    self.program_state.gui_state.output_dir = os.path.dirname(file_path)
                    self.program_state.gui_state.initial_filename = Path(file_path).stem
                    self.program_state.initialize_from_piece_properties(piece_properties)
                    right_increment_decrement_widget.set_counter(self.program_state.gui_state.number_of_pages.get())
                    try:  ## TODO
                        self.program_state.gui_state.tk_current_mode_string.set(GongdiaoModeList.from_properties(self.program_state.piece_properties.mode_properties).name)
                    except Exception:
                        self.program_state.gui_state.tk_current_mode_string.set("NO MODE")
                    self.program_state.gui_state.tk_notation_plugin_selection.set(json_contents["notation_type"])
                    self.program_state.gui_state.tk_current_composer.set(json_contents["composer"])

                    annotation_frame.set_mode_properties(self.program_state.piece_properties.mode_properties)

                    self.program_state.gui_state.image_name_circle.set_if_present(os.path.join(self.program_state.gui_state.images_dir, Path(piece_properties.base_image_path).name))
                    must_be_changed()
                    on_activate_deactivate_annotation_frame()

        prev_next_increment_frame = tk.Frame(self.main_window)
        increment_decrement_subframe = tk.LabelFrame(prev_next_increment_frame, text="Number of Pages")
        previous_next = PreviousNextFrame(prev_next_increment_frame, self.program_state.gui_state.tk_current_filename, on_previous, on_next).get_frame()
        right_increment_decrement_widget = IncrementDecrementFrame(increment_decrement_subframe, self.program_state.gui_state.number_of_pages, must_be_changed)
        right_increment_decrement = right_increment_decrement_widget.get_frame()
        previous_next.grid(row=0, column=0)

        right_increment_decrement.pack(pady=3)
        increment_decrement_subframe.grid(row=0, column=1)

        segmentation_frame = tk.LabelFrame(self.main_window, text="Segmentation and Order")
        inner_frame = tk.Frame(segmentation_frame)
        #invert_order_checkbutton = tk.Checkbutton(checkbox_options_frame, text='Invert order', variable=self.gui_state.gui_state.self.gui_state.gui_state.tk_display_images_in_reversed_order,
        #                                          onvalue=1, offvalue=0, command=must_be_changed)
        segment_pages_individually_checkbutton = tk.Checkbutton(inner_frame, text='Segment individually',
                                                                variable=self.program_state.gui_state.tk_segmentation_individual_pages, onvalue=1,
                                                                offvalue=0, command=must_be_changed)
        segmentation_button = tk.Button(inner_frame, text="Auto-Segmentation", command=self.program_state.make_new_segmentation)
        infer_order_button = tk.Button(inner_frame, text="Infer Box Order and Column Breaks", command=on_infer_order)
        min_bounding_rect = tk.Button(inner_frame, text="Min Bounding Rectangles", command=on_min_bounding_rect)
        segmentation_button.grid(row=0, column=0)
        min_bounding_rect.grid(row=0, column=1)
        infer_order_button.grid(row=0, column=2)
        segment_pages_individually_checkbutton.grid(row=1, column=0)
        inner_frame.pack(padx=10, pady=3)

        save_load_buttons = SaveLoadFrame(self.main_window, on_save_image, on_new, on_save, on_save_text, on_load).get_frame()
        annotation_frame = AnnotationFrame(self.main_window, self.program_state)

        notation_window = tk.Toplevel()
        notation_window.title("Suzipu Musical Annotation Tool - Notation Display")
        notation_window.protocol("WM_DELETE_WINDOW", lambda: None)
        notation_window.resizable(False, False)
        #display_notes_frame = AdditionalInfoFrame(notation_window, self.gui_state.gui_state.tk_current_mode_string, on_save_notation, on_save_musicxml, self.program_state.get_mode_string)
        display_notes_frame = DisplayNotesFrame(notation_window, on_save_notation, on_save_musicxml)

        def reset_annotation_vars():
            self.program_state.gui_state.tk_current_box_annotation.set("")
            self.program_state.gui_state.tk_current_box_out_of_current_type.set(None)
            self.program_state.gui_state.tk_num_all_boxes_of_current_type.set(None)
            self.program_state.gui_state.tk_current_box_is_excluded.set(False)
            self.program_state.gui_state.tk_current_box_is_line_break.set(False)
            annotation_frame.set_image(None)

        def handle_notation_info():
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

            plugin_name = self.program_state.gui_state.tk_notation_plugin_selection.get().lower()
            module = importlib.import_module(f"src.plugins.{plugin_name}")

            if module.DISPLAY_NOTATION:
                notation_img = get_notation_image()

                if notation_img:
                    notation_img = resize_to_width(notation_img)
                    notation_img = ImageTk.PhotoImage(image=notation_img)
                    display_notes_frame.set_image(notation_img)
                else:
                    display_notes_frame.set_image(invalid_mode_image)

                if self.program_state.gui_state.tk_current_action.get() == BoxManipulationAction.ANNOTATE:
                    display_notes_frame.set_state(True)
                else:
                    display_notes_frame.set_state(False)
                    display_notes_frame.set_image(go_into_annotation_mode_image)
            else:
                display_notes_frame.set_state(False)
                display_notes_frame.set_image(plugin_not_support_notation_image)

        def start_opencv_timer():
            handle_opencv_window()
            self.main_window.after(1, start_opencv_timer)

        def start_notation_window_timer():
            handle_notation_info()
            self.main_window.after(100, start_notation_window_timer)

        def on_activate_deactivate_annotation_frame():
            state = self.program_state.gui_state.tk_current_action.get() == BoxManipulationAction.ANNOTATE and selection_buttons.is_active and len(self.program_state.gui_state.type_to_cycle_dict[self.program_state.gui_state.tk_current_boxtype.get()].list) > 0
            annotation_frame.set_state(state)

        subframe = tk.Frame(self.main_window)
        selection_buttons = SelectionFrame(subframe, self.program_state, self.program_state.gui_state.tk_current_action, self.program_state.gui_state.tk_current_boxtype, on_click_annotate,
                                           lambda: [on_activate_deactivate_annotation_frame(), annotation_frame.update_annotation()],
                                           lambda: [self.program_state.update_annotation_image_and_variables(), on_activate_deactivate_annotation_frame(), annotation_frame.update_annotation()])
        piece_properties = PiecePropertiesFrame(subframe, self.program_state)
        selection_buttons.get_frame().grid(row=0, column=0, padx=3)
        piece_properties.get_frame().grid(row=0, column=1, padx=3)
        save_load_buttons.grid(row=0, column=1, pady=3)

        prev_next_increment_frame.grid(row=1, column=1, padx=10, pady=3)

        segmentation_frame.grid(row=2, column=1, pady=3)
        subframe.grid(row=4, column=1, pady=3)
        annotation_frame.get_frame().grid(row=5, column=1, padx=10, pady=3)

        display_notes_frame.get_frame().grid(row=6, column=1)

        self.main_window.after(1, start_opencv_timer)
        self.main_window.after(1, start_notation_window_timer)

        def _on_closing():
            on_closing(self.main_window)()

        self.main_window.protocol("WM_DELETE_WINDOW", _on_closing)

        annotation_frame.set_image(self.program_state.gui_state.empty_image)

        self.main_window.mainloop()


class OpenCvWindow:
    def __init__(self, window_name, program_state):
        self.window_name = window_name
        self.program_state = program_state
        self.current_mouse_coordinates = None
        self.current_move_box_idx = None
        self.move_direction = None
        self.current_move_box = None
        self.draw_image = None
        self.point_1 = None
        self.point_2 = None
        self.is_clicked = False
        self.segmentation_boxes = BoxesWithType()

        cv2.namedWindow(self.window_name, cv2.WINDOW_GUI_NORMAL)
        cv2.resizeWindow(self.window_name, 600, 600)
        cv2.setMouseCallback(self.window_name, self.handle_mouse_events)

    def __del__(self):
        cv2.destroyWindow(self.window_name)

    def handle_mouse_events(self, event, x, y, flags, param):
        if event == cv2.EVENT_RBUTTONDOWN:
            self.point_1 = (x, y)
            self.is_clicked = True

        if event == cv2.EVENT_RBUTTONUP:
            if self.point_1 is not None:
                self.point_2 = (x, y)
            self.is_clicked = False

        if event == cv2.EVENT_MOUSEMOVE:
            self.current_mouse_coordinates = (x, y)

    def draw_and_handle_clicks(self, program_state, selection_mode, boxtype, current_image, current_annotation_idx, set_current_annotation_idx = lambda: None):
        self.segmentation_boxes = program_state.content

        exit_flag = False
        self.draw_image = copy.deepcopy(current_image)

        keypress = cv2.waitKey(1)
        # exit if q is pressed or the red x button in the window
        if keypress == ord('q'): #or cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
            exit_flag = True

        if self.current_mouse_coordinates and self.is_clicked and selection_mode in [BoxManipulationAction.MARK, BoxManipulationAction.DELETE, BoxManipulationAction.ANNOTATE]:
            if program_state.content:
                for idx, box in enumerate(program_state.content.get_coordinates()):
                    if is_point_in_rectangle(self.current_mouse_coordinates, box):
                        if selection_mode == BoxManipulationAction.MARK:
                            program_state.content.set_index_type(idx, boxtype)
                        if selection_mode == BoxManipulationAction.DELETE:
                            program_state.content.delete_index(idx)
                        if selection_mode == BoxManipulationAction.ANNOTATE:
                            set_current_annotation_idx(idx)
                        break

        if selection_mode == BoxManipulationAction.CREATE:
            if self.point_1 is not None:
                self.draw_image = draw_transparent_rectangle(self.draw_image, self.point_1, self.current_mouse_coordinates,
                                                Colors.VIOLET, 1, 0.8)
                if self.point_1 is not None and self.point_2 is not None:
                    if is_rectangle_big_enough([self.point_1, self.point_2]):
                        self.segmentation_boxes.add_rectangle(self.point_1, [self.point_2[0]+1, self.point_2[1]+1], type=boxtype)
                    self.point_1 = None
                    self.point_2 = None
            else:  # draw ruler
                if self.current_mouse_coordinates is not None:
                    current_x, current_y = self.current_mouse_coordinates
                    self.draw_image = draw_transparent_line(self.draw_image, (current_x-2, current_y), (current_x+40, current_y), Colors.VIOLET, 1, alpha=0.3)
                    self.draw_image = draw_transparent_line(self.draw_image, (current_x, current_y-2), (current_x, current_y+40), Colors.VIOLET, 1, alpha=0.3)
        elif selection_mode == BoxManipulationAction.MOVE_RESIZE:
            if self.current_move_box_idx is None:
                if self.point_1 is not None:
                    for idx, box in enumerate(program_state.content.get_coordinates()):
                        if is_point_in_rectangle(self.point_1, box):
                            self.current_move_box_idx = idx
                            top_y = max(box[0][1], box[1][1])
                            bottom_y = min(box[0][1], box[1][1])
                            left_x = min(box[0][0], box[1][0])
                            right_x = max(box[0][0], box[1][0])

                            PIXEL_DIFF_FOR_MOVE = 4
                            if abs(self.point_1[0] - left_x) < PIXEL_DIFF_FOR_MOVE:
                                self.move_direction = "LEFT"
                            elif abs(self.point_1[0] - right_x) < PIXEL_DIFF_FOR_MOVE:
                                self.move_direction = "RIGHT"
                            elif abs(self.point_1[1] - top_y) < PIXEL_DIFF_FOR_MOVE:
                                self.move_direction = "BOTTOM"
                            elif abs(self.point_1[1] - bottom_y) < PIXEL_DIFF_FOR_MOVE:
                                self.move_direction = "TOP"
                            else:
                                self.move_direction = "MOVE"
                            break
                    if self.move_direction is None:
                        self.point_1 = None
                        self.point_2 = None
            else:
                current_coords = self.segmentation_boxes.get_index_coordinates(self.current_move_box_idx)

                def get_increments(point2, move_direction):
                    draw_increment = [0, 0, 0, 0]
                    if move_direction == "LEFT":
                        draw_increment[0] = point2[0] - self.point_1[0]
                    elif move_direction == "RIGHT":
                        draw_increment[2] = point2[0] - self.point_1[0]
                    elif move_direction == "TOP":
                        draw_increment[1] = point2[1] - self.point_1[1]
                    elif move_direction == "BOTTOM":
                        draw_increment[3] = point2[1] - self.point_1[1]
                    return draw_increment

                if self.move_direction is not None and self.move_direction != "MOVE":  # Resize mode
                    draw_increment = get_increments(self.current_mouse_coordinates, self.move_direction)
                    self.draw_image = cv2.rectangle(self.draw_image, [current_coords[0][0] + draw_increment[0],
                                                                      current_coords[0][1] + draw_increment[1]],
                                                    [current_coords[1][0] + draw_increment[2] - 1,
                                                     current_coords[1][1] + draw_increment[3] - 1],
                                                    Colors.VIOLET, 1)

                    if self.point_1 is not None and self.point_2 is not None:
                        increment = get_increments(self.current_mouse_coordinates, self.move_direction)
                        self.segmentation_boxes.set_index_coordinates(self.current_move_box_idx, [
                            [current_coords[0][0] + increment[0], current_coords[0][1] + increment[1]],
                            [current_coords[1][0] + increment[2], current_coords[1][1] + increment[3]]
                        ])
                        self.point_1 = None
                        self.point_2 = None
                        self.current_move_box_idx = None
                        self.move_direction = None

                elif self.move_direction is not None:  # Move mode
                    draw_increment = (self.current_mouse_coordinates[0] - self.point_1[0], self.current_mouse_coordinates[1] - self.point_1[1])
                    self.draw_image = cv2.rectangle(self.draw_image, [current_coords[0][0] + draw_increment[0], current_coords[0][1] + draw_increment[1]],
                            [current_coords[1][0] + draw_increment[0] - 1, current_coords[1][1] + draw_increment[1] - 1],
                                                    Colors.VIOLET, 1)
                    if self.point_1 is not None and self.point_2 is not None:
                        increment = (self.point_2[0] - self.point_1[0], self.point_2[1] - self.point_1[1])
                        self.segmentation_boxes.set_index_coordinates(self.current_move_box_idx, [
                            [current_coords[0][0] + increment[0], current_coords[0][1] + increment[1]],
                            [current_coords[1][0] + increment[0], current_coords[1][1] + increment[1]]
                        ])
                        self.current_move_box_idx = None
                        self.point_1 = None
                        self.point_2 = None
                        self.move_direction = None
                else:
                    self.current_move_box_idx = None
                    self.point_1 = None
                    self.point_2 = None
                    self.move_direction = None
        else:
            self.point_1 = None
            self.point_2 = None
            self.move_direction = None

        if program_state.content:
            for idx in range(len(program_state.content.get_coordinates())):
                start, end = program_state.content.get_index_coordinates(idx)
                if current_annotation_idx is not None and idx == current_annotation_idx:  #currently selected box should be drawn thicker
                    self.draw_image = cv2.rectangle(self.draw_image, start, [end[0]-1, end[1]-1], Colors.VIOLET, 8)
                else:
                    self.draw_image = cv2.rectangle(self.draw_image, start, [end[0]-1, end[1]-1], box_property_to_color(
                        program_state.content.get_index_type(idx)), self.program_state.gui_state.draw_box_width.get())


        cv2.imshow(self.window_name, self.draw_image)
        return self.segmentation_boxes, exit_flag

    def get_current_draw_image(self):
        return self.draw_image


if __name__ == "__main__":
    weights_path = "./weights/HRCenterNet.pth.tar"

    if not os.path.isfile(weights_path):
        showerror("Error", "'HRCenterNet.pth.tar' could not be found. Please download the file 'HRCenterNet.pth.tar' and put it into the folder 'weights'. Abort.")
        exit(-1)

    main_window = MainWindow(weights_path)
    main_window.exec()
