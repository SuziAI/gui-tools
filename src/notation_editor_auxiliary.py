import dataclasses
import importlib
import json
import os.path
import tkinter as tk
from tkinter import filedialog
from tkinter.filedialog import asksaveasfilename

import cv2
import jsonschema
import numpy as np

from src.auxiliary import is_rectangle_big_enough, pil_to_cv, is_point_in_rectangle, BoxType, open_file_as_tk_image
from src.config import NOTATION_BUTTON_IMAGE, JIANPU_BUTTON_IMAGE, FIVELINE_BUTTON_IMAGE
from src.plugins import NotationTypePlugins
from src.plugins.suzipu_lvlvpu_gongchepu.notes_to_image import vertical_composition, construct_metadata_image, \
    NotationResources, add_border, Fingering, apply_border_to_boxes, \
    horizontal_composition, write_to_musicxml
from src.plugins.suzipu_lvlvpu_gongchepu.common import GongdiaoMode, GongdiaoModeList, \
    _create_suzipu_images, Symbol, SuzipuAdditionalSymbol, SuzipuMelodySymbol


PLUGINS = NotationTypePlugins()


@dataclasses.dataclass
class DisplayType:
    JIANPU: str = "Jianpu"
    STAFF: str = "Fiveline"
    NOTATION_SPECIFIC: str = "Notation-Specific"


class WindowStateService:
    def __init__(self):
        self.dictionary = {}

    def is_registered(self, key):
        is_regi = False
        try:
            is_regi = self.dictionary[key]
        except:
            pass
        return is_regi

    def register(self, key):
        self.dictionary[key] = True

    def unregister(self, key):
        self.dictionary[key] = False


window_state_service = WindowStateService()


class MusicBox:
    lyrics: str
    note: dict
    line_break: bool

    def __init__(self, lyrics, note, line_break):
        self.lyrics = lyrics
        self.note = note
        self.line_break = line_break


class MusicBoxList:
    def __init__(self, listbox: tk.Listbox, music_box_list=[]):
        self.list: list[MusicBox] = None
        self.listbox = listbox
        self.set(music_box_list)

    def build_display(self):
        for idx, box in enumerate(self.list):
            line_break_str = "¶" if box.line_break else ""

            note_str = ""

            if type(box.note) is dict:
                if "pitch" in box.note:
                    note_str = box.note["pitch"]
                if "secondary" in box.note:
                    if box.note["secondary"]:
                        note_str += f' {box.note["secondary"]}'

            self.listbox.insert(idx, f"{str(idx+1)+'.':<5} {str(box.lyrics):<3} {str(note_str):<6} {str(line_break_str)}")
        if len(self.list) > 0:
            self.listbox.delete(idx+1, tk.END)

    def append_element(self, box: MusicBox):
        self.list.append(box)
        self.build_display()

    def set_cursor(self, idx):
        self.listbox.selection_clear(0, tk.END)
        if idx >= 0:  # set cursor
            self.listbox.select_set(idx)
            self.listbox.see(idx)
        else:
            self.listbox.select_set(0)
            self.listbox.see(0)
        self.listbox.event_generate("<<ListboxSelect>>")

    def insert_element(self, idx, box: MusicBox):
        self.list.insert(idx, box)
        self.build_display()
        self.set_cursor(idx)

    def modify_element(self, idx, box: MusicBox):
        self.list[idx] = box
        self.build_display()
        self.set_cursor(idx)

    def delete_element(self, idx):
        try:
            del self.list[idx]
            self.listbox.delete(idx)
            self.build_display()
            self.set_cursor(idx-1)
        except IndexError:
            pass

    def set(self, l: list[MusicBox]):
        self.reset()
        for box in l:
            self.append_element(box)

    def reset(self):
        self.list = []
        self.listbox.delete(0, tk.END)

    def get_element(self, idx) -> MusicBox:
        try:
            return self.list[idx]
        except IndexError:
            pass


class DisplayState:
    def __init__(self, frame, plugin_name=None):
        self.transposition = Fingering.ALL_CLOSED_AS_1
        self.music_listframe = tk.LabelFrame(frame, text="Select note")
        self.notation_resources = NotationResources()
        self.is_vertical = tk.BooleanVar(value=False)

        self.plugin_name = plugin_name
        self.display_type = tk.StringVar(frame, DisplayType.NOTATION_SPECIFIC)

        self.last_directory = ""
        self.last_filename = None

        self._music_listbox = None
        self._new_button = None
        self._delete_button = None

        self.image_to_save = None
        self.image_to_draw = None
        self.idx_boxes = None

        self.config_music_listframe()

    def config_music_listframe(self):
        frame = tk.Frame(self.music_listframe)

        listbox_frame = tk.Frame(frame)
        self._music_listbox = tk.Listbox(listbox_frame)
        self._music_listbox.pack(side=tk.LEFT, fill=tk.BOTH)
        self._music_listbox.configure(exportselection=False)
        music_scrollbar = tk.Scrollbar(listbox_frame)
        self._music_listbox.config(yscrollcommand=music_scrollbar.set)
        music_scrollbar.config(command=self._music_listbox.yview)
        music_scrollbar.pack(side=tk.RIGHT, fill=tk.BOTH)
        listbox_frame.pack()

        buttons = tk.Frame(frame)
        self._new_button = tk.Button(buttons, text="New note")
        self._new_button.grid(row=0, column=0)
        self._delete_button = tk.Button(buttons, text="Delete note")
        self._delete_button.grid(row=0, column=1)

        buttons.pack(side=tk.BOTTOM)
        frame.pack(padx=5, pady=5)

    def update_image(self, notation_state):
        def get_notation_image():
            music_list = []
            lyrics_list = []
            line_break_idxs = []
            for idx, box in enumerate(notation_state.music_boxes.list):
                music_list.append(box.note)
                lyrics_list.append(box.lyrics)
                if box.line_break:
                    line_break_idxs.append(idx)

            plugin_name = self.plugin_name.get().lower()
            module = importlib.import_module(f"src.plugins.{plugin_name}")

            if module.DISPLAY_NOTATION:
                if self.display_type.get() == DisplayType.JIANPU:
                    notation_func = module.notation_to_jianpu
                elif self.display_type.get() == DisplayType.STAFF:
                    notation_func = module.notation_to_staff
                elif self.display_type.get() == DisplayType.NOTATION_SPECIFIC:
                    notation_func = module.notation_to_own
                else:
                    notation_func = module.notation_to_own
            else:
                notation_func = module.notation_to_own

            notation_img, boxes = notation_func(
                GongdiaoModeList.from_properties(notation_state.get_mode_properties()),
                music_list, lyrics_list,
                line_break_idxs,
                self.transposition,
                True,
                notation_state.display_state.is_vertical.get()
            )

            return notation_img, boxes

        def get_metadata_image(img_width):
            metadata_img = construct_metadata_image(self.notation_resources.title_font,
                                                    self.notation_resources.small_font,
                                                    notation_state.title.get(),
                                                    notation_state.mode_name.get(),
                                                    notation_state.preface.get(),
                                                    image_width=img_width,
                                                    composer=notation_state.composer.get(),
                                                    is_vertical=notation_state.display_state.is_vertical.get())
            return metadata_img
        notation_img, boxes = get_notation_image()

        if notation_img is None:
            return None

        metadata_img = get_metadata_image(notation_img.width)
        if notation_state.display_state.is_vertical.get():
            combined_img = horizontal_composition([notation_img, metadata_img])
            boxes = apply_border_to_boxes(boxes, 150 // 2, 200 // 2)
        else:
            combined_img = vertical_composition([metadata_img, notation_img])
            boxes = apply_border_to_boxes(boxes, 150 // 2, 200 // 2 + metadata_img.height)
        combined_img = add_border(combined_img, 150, 200)
        self.image_to_save, self.idx_boxes = pil_to_cv(combined_img), boxes


class NotationState:
    def __init__(self, frame, display_state: DisplayState):
        self.display_state = display_state

        self.version = "2.0"
        self.notation_type = tk.StringVar(frame)
        self.notation_type.set("Text")
        self.composer = tk.StringVar()
        self.title = tk.StringVar(frame)
        self.preface = tk.StringVar(frame)
        self.unmarked = tk.StringVar(frame)
        self.mode_name = tk.StringVar(frame)
        self.music_boxes = MusicBoxList(self.display_state._music_listbox)

        self.get_mode_properties = lambda: None
        self.set_mode_properties = None

        def new_box():
            idx = self.get_current_selection()
            if idx is not None:
                self.music_boxes.insert_element(idx + 1, MusicBox("", "", False))
            else:
                self.music_boxes.append_element(MusicBox("", "", False))

        def delete_box():
            current_idx = self.get_current_selection()
            if current_idx is not None:
                self.music_boxes.delete_element(current_idx)

        self.display_state._new_button.config(command=new_box)
        self.display_state._delete_button.config(command=delete_box)

    def get_current_selection(self):
        for idx in self.display_state._music_listbox.curselection():
            return idx
        return None

    def reset(self):
        self.notation_type.set("Text")
        self.composer.set("")
        self.title.set("")
        self.preface.set("")
        self.unmarked.set("")
        self.mode_name.set("")
        self.music_boxes.reset()


def construct_new_frame_from_label(frame, label=None):
    if label is None:
        return tk.Frame(frame)
    else:
        return tk.LabelFrame(frame, text=label)


class BasicFrame:
    def __init__(self, frame, label):
        self.subframe = construct_new_frame_from_label(frame, label)

    def get_frame(self):
        return self.subframe


class NewSaveLoadFrame(BasicFrame):
    def __init__(self, frame, notation_state: NotationState, label=None):
        def load_json_schema(file_path):
            with open(file_path, "r") as schema_file:
                return json.load(schema_file)

        super().__init__(frame, label)
        self.notation_state = notation_state
        self.json_schema = load_json_schema("json_schema.json")
        self.get_mode_properties = None

        self._initialize()

    def _initialize(self):
        def on_new_file():
            self.notation_state.reset()
            self.notation_state.display_state.update_image(self.notation_state)

        def on_open_file():
            def extract_string_from_content(content, box_type):
                string = ""
                for box in content:
                    if box["box_type"] == box_type:
                        try:
                            string += box["text_content"]
                        except KeyError:
                            pass
                        try:
                            if box["is_line_break"]:
                                string += "\n"
                        except KeyError:
                            pass
                return string

            def extract_music_boxes_from_content(content):
                music_list = []
                for box in content:
                    if box["box_type"] == BoxType.MUSIC:
                        try:
                            text = box["text_content"]
                        except KeyError:
                            text = ""
                        try:
                            notation = box["notation_content"]
                        except KeyError:
                            notation = ""

                        try:
                            line_break = box["is_line_break"]
                        except KeyError:
                            line_break = False

                        music_list.append(MusicBox(text, notation, line_break))
                return music_list

            filetypes = (
                ('recommended files', '*.json'),
                ('All files', '*.*')
            )
            json_path = filedialog.askopenfilename(
                title='Open notation file',
                initialdir=self.notation_state.display_state.last_directory,
                filetypes=filetypes
            )

            if json_path:
                with open(json_path, "r") as json_file:
                    json_data = json.load(json_file)
                    jsonschema.validate(json_data, self.json_schema)
                    self.notation_state.display_state.last_directory = os.path.dirname(json_path)
                    self.notation_state.display_state.last_filename = os.path.splitext(os.path.basename(json_path))[0]

                    self.notation_state.notation_type.set(json_data["notation_type"])
                    self.notation_state.composer.set(json_data["composer"])
                    self.notation_state.title.set(extract_string_from_content(json_data["content"], BoxType.TITLE))
                    self.notation_state.preface.set(extract_string_from_content(json_data["content"], BoxType.PREFACE))
                    self.notation_state.unmarked.set(extract_string_from_content(json_data["content"], BoxType.UNMARKED))
                    self.notation_state.mode_name.set(extract_string_from_content(json_data["content"], BoxType.MODE))
                    self.notation_state.set_mode_properties(json_data["mode_properties"])
                    self.notation_state.music_boxes.set(extract_music_boxes_from_content(json_data["content"]))

                    if len(self.notation_state.music_boxes.list) > 0:
                        self.notation_state.music_boxes.set_cursor(0)

                    self.notation_state.display_state.update_image(self.notation_state)

        def on_save_file():
            mode_properties = None
            if self.notation_state.get_mode_properties:
                mode_properties = self.notation_state.get_mode_properties()

            def notation_state_to_dict(notation_state: NotationState):
                content = []

                content += [{
                    "box_type": BoxType.TITLE,
                    "text_content": self.notation_state.title.get(),
                }, {
                    "box_type": BoxType.MODE,
                    "text_content": self.notation_state.mode_name.get(),
                }, {
                    "box_type": BoxType.PREFACE,
                    "text_content": self.notation_state.preface.get(),
                }, {
                        "box_type": BoxType.UNMARKED,
                        "text_content": self.notation_state.unmarked.get(),
                    }
                ]

                content += [{
                    "box_type": BoxType.MUSIC,
                    "text_content": music_box.lyrics,
                    "notation_content": music_box.note,
                    "is_line_break": music_box.line_break,
                } for music_box in notation_state.music_boxes.list]

                return {
                    "version": notation_state.version,
                    "notation_type": notation_state.notation_type.get(),
                    "composer": notation_state.composer.get(),
                    "mode_properties": mode_properties,
                    "content": content
                }

            initial_filename = self.notation_state.display_state.last_filename
            if initial_filename is None or initial_filename == "":
                initial_filename = self.notation_state.title.get()

            file_path = asksaveasfilename(
                initialdir=self.notation_state.display_state.last_directory,
                initialfile=initial_filename,
                defaultextension=".json",
                filetypes=[("JSON File", "*.json"), ("All Files", "*.*")])
            if file_path:
                with open(file_path, "w") as json_file:
                    self.notation_state.display_state.last_directory = os.path.dirname(file_path)
                    self.notation_state.display_state.last_filename = os.path.splitext(os.path.basename(file_path))[0]
                    json_state = notation_state_to_dict(self.notation_state)
                    jsonschema.validate(json_state, self.json_schema)
                    json.dump(json_state, json_file)

        tk.Button(self.subframe, text="New File", command=on_new_file).grid(row=0, column=0)
        tk.Button(self.subframe, text="Open File", command=on_open_file).grid(row=0, column=1)
        tk.Button(self.subframe, text="Save File", command=on_save_file).grid(row=0, column=2)


class EditMetadataButton(BasicFrame):
    def __init__(self, frame, notation_state: NotationState, label=None):
        super().__init__(frame, label)
        self.notation_state = notation_state

        self._initialize()

    def _on_execute_metadata_window(self):
        window_key = "METADATA"

        if not window_state_service.is_registered(window_key):
            window_state_service.register(window_key)
            metadata_window = tk.Toplevel()
            metadata_window.title(f"Edit Metadata...")
            metadata_window.protocol("WM_DELETE_WINDOW", lambda: [window_state_service.unregister(window_key), metadata_window.destroy()])

            top_frame = tk.Frame(metadata_window)

            composer = tk.StringVar(top_frame, value=self.notation_state.composer.get())
            title = tk.StringVar(top_frame, value=self.notation_state.title.get())
            mode_name = tk.StringVar(top_frame, value=self.notation_state.mode_name.get())
            preface = tk.StringVar(top_frame, value=self.notation_state.preface.get())
            unmarked = tk.StringVar(top_frame, value=self.notation_state.unmarked.get())

            def get_text_metadata_frame():
                text_metadata_frame = tk.Frame(top_frame)
                tk.Label(text_metadata_frame, text="Composer").grid(row=0, column=0)
                tk.Entry(text_metadata_frame, textvariable=composer, font="Arial 15",).grid(row=0, column=1)

                tk.Label(text_metadata_frame, text="Title").grid(row=1, column=0)
                tk.Entry(text_metadata_frame, textvariable=title, font="Arial 15",).grid(row=1, column=1)

                tk.Label(text_metadata_frame, text="Mode Information").grid(row=2, column=0)
                tk.Entry(text_metadata_frame, textvariable=mode_name, font="Arial 15", ).grid(row=2, column=1)

                def on_trace_preface(*args):
                    preface.set(preface_field.get("1.0", tk.END))

                def on_trace_unmarked(*args):
                    unmarked.set(unmarked_field.get("1.0", tk.END))

                tk.Label(text_metadata_frame, text="Preface").grid(row=3, column=0)
                preface_field = tk.Text(text_metadata_frame, width=20, height=3, font="Arial 15")
                preface_field.insert(tk.END, preface.get())
                preface_field.bind('<KeyRelease>', on_trace_preface)
                preface_field.grid(row=3, column=1)

                tk.Label(text_metadata_frame, text="Unmarked").grid(row=4, column=0)
                unmarked_field = tk.Text(text_metadata_frame, width=20, height=3, font="Arial 15")
                unmarked_field.insert(tk.END, unmarked.get())
                unmarked_field.bind('<KeyRelease>', on_trace_unmarked)
                unmarked_field.grid(row=5, column=1)

                return text_metadata_frame

            get_text_metadata_frame().grid(row=0, column=0)

            def on_destroy_save_changes():
                self.notation_state.composer.set(composer.get())
                self.notation_state.title.set(title.get())
                self.notation_state.mode_name.set(mode_name.get())
                self.notation_state.preface.set(preface.get())
                self.notation_state.unmarked.set(unmarked.get())
                self.notation_state.display_state.update_image(self.notation_state)
                window_state_service.unregister(window_key)
                metadata_window.destroy()

            buttons_frame = tk.Frame(top_frame)
            tk.Button(buttons_frame, text="OK", command=on_destroy_save_changes).grid(row=0, column=0)
            tk.Button(buttons_frame, text="Cancel", command=lambda: [window_state_service.unregister(window_key), metadata_window.destroy()]).grid(row=0, column=1)
            buttons_frame.grid(row=2, column=0)

            top_frame.pack(padx=10, pady=10)
            metadata_window.wait_window()

    def _initialize(self):
        tk.Button(self.subframe, text="Edit Metadata...", command=self._on_execute_metadata_window).pack()


class DisplayOptionsFrame(BasicFrame):
    def __init__(self, frame, notation_state: NotationState):
        super().__init__(frame, "Display options")
        self.notation_image = open_file_as_tk_image(NOTATION_BUTTON_IMAGE)
        self.jianpu_image = open_file_as_tk_image(JIANPU_BUTTON_IMAGE)
        self.fiveline_image = open_file_as_tk_image(FIVELINE_BUTTON_IMAGE)

        self.jianpu_button = None
        self.staff_button = None

        self.notation_state = notation_state

        self._initialize()

    def _initialize(self):
        frame = tk.Frame(self.subframe)
        transposition_string = tk.StringVar(value=Fingering.ALL_CLOSED_AS_1.name)

        def update_image(*args):
            self.notation_state.display_state.update_image(self.notation_state)

        def on_change_transposition(*args):
            self.notation_state.display_state.transposition = Fingering.from_string(transposition_string.get())
            update_image()

        def update(*args):
            update_image()
            vertical_checkbox.config(state="normal" if self.notation_state.display_state.display_type.get() == DisplayType.NOTATION_SPECIFIC else "disabled")
            if self.notation_state.display_state.display_type.get() != DisplayType.NOTATION_SPECIFIC:
                self.notation_state.display_state.is_vertical.set(False)

        options_frame = tk.Frame(frame)

        notation_button = tk.Radiobutton(options_frame, image=self.notation_image, variable=self.notation_state.display_state.display_type,
                                         value=DisplayType.NOTATION_SPECIFIC,
                                         indicator=0, command=update)
        self.jianpu_button = tk.Radiobutton(options_frame, image=self.jianpu_image, variable=self.notation_state.display_state.display_type,
                                       value=DisplayType.JIANPU,
                                       indicator=0, command=update)
        self.staff_button = tk.Radiobutton(options_frame, image=self.fiveline_image, variable=self.notation_state.display_state.display_type,
                                      value=DisplayType.STAFF,
                                      indicator=0, command=update)

        notation_button.grid(row=1, column=0)
        self.jianpu_button.grid(row=1, column=1)
        self.staff_button.grid(row=1, column=2)

        transpositions = tk.OptionMenu(options_frame, transposition_string, *[fingering.name for fingering in dataclasses.astuple(Fingering())], command=on_change_transposition)
        transpositions.grid(row=1, column=3)

        vertical_checkbox = tk.Checkbutton(options_frame, text="Trad. Reading Order", variable=self.notation_state.display_state.is_vertical, command=update_image)
        vertical_checkbox.grid(row=1, column=4)
        options_frame.grid(row=0, column=0)

        def export_image():
            draw_image = self.notation_state.display_state.image_to_save
            if draw_image is not None:
                initialfile = self.notation_state.display_state.last_filename
                if initialfile == "" or initialfile is None:
                    initialfile = self.notation_state.title.get()
                file_path = asksaveasfilename(
                    initialdir=self.notation_state.display_state.last_directory,
                    initialfile=initialfile,
                    defaultextension=".png",
                    filetypes=[("PNG File", "*.png"), ("All Files", "*.*")])
                if file_path:
                    cv2.imwrite(file_path, draw_image)

        def save_to_musicxml(file_path):
            mode = GongdiaoModeList.from_properties(self.notation_state.get_mode_properties())

            music_list = []
            lyrics_list = []
            line_break_idxs = []
            for idx, box in enumerate(self.notation_state.music_boxes.list):
                music_list.append(box.note)
                lyrics_list.append(box.lyrics)
                if box.line_break:
                    line_break_idxs.append(idx)

            try:
                music_list = mode.convert_pitches_in_list(music_list)
            except TypeError:  # This happens when the chosen mode does not match the piece
                return None

            fingering = self.notation_state.display_state.transposition

            title = self.notation_state.title.get()
            mode_str = self.notation_state.mode_name.get()
            preface = self.notation_state.preface.get()

            write_to_musicxml(file_path, music_list, lyrics_list, fingering, title, mode_str, preface)

        def export_musicxml():
            initialfile = self.notation_state.display_state.last_filename
            if initialfile == "" or initialfile is None:
                initialfile = self.notation_state.title.get()
            file_path = asksaveasfilename(
                initialdir=self.notation_state.display_state.last_directory,
                initialfile=initialfile,
                defaultextension=".musicxml",
                filetypes=[("MusicXML File", "*.musicxml"), ("All Files", "*.*")])
            if file_path:
                save_to_musicxml(file_path)

        export_frame = tk.Frame(frame)
        tk.Button(export_frame, text="Export Image", command=export_image).grid(row=0, column=0)
        tk.Button(export_frame, text="Export MusicXML", command=export_musicxml).grid(row=0, column=1)
        export_frame.grid(row=2, column=0)

        def update_vertical_and_transposition(*args):
            # modern notations do not support vertical display
            if self.notation_state.display_state.display_type.get() != DisplayType.NOTATION_SPECIFIC:
                self.notation_state.display_state.is_vertical.set(False)
                vertical_checkbox.config(state="disabled")
                transpositions.config(state="normal")
            else:
                vertical_checkbox.config(state="normal")
                transpositions.config(state="disabled")

        def update_notation_type(*args):
            plugin_name = self.notation_state.notation_type.get().lower()
            module = importlib.import_module(f"src.plugins.{plugin_name}")
            self.notation_state.display_state.display_type.set(DisplayType.NOTATION_SPECIFIC)
            self.jianpu_button.config(state="normal" if hasattr(module, 'notation_to_jianpu') else "disabled")
            self.staff_button.config(state="normal" if hasattr(module, 'notation_to_staff') else "disabled")

        self.notation_state.display_state.display_type.trace_add("write", update_vertical_and_transposition)
        self.notation_state.notation_type.trace_add("write", update_notation_type)

        frame.pack(padx=5, pady=5)


class NotationOptionMenu(BasicFrame):
    def __init__(self, frame, notation_state: NotationState, label=None):
        super().__init__(frame, label)
        self.notation_state = notation_state
        self.initialize()

    def initialize(self):
        notation_type = tk.StringVar(value=self.notation_state.notation_type.get())

        def update_notation(*args):
            notation_type.set(self.notation_state.notation_type.get())
        self.notation_state.notation_type.trace_add("write", update_notation)

        def on_change_notation(*args):
            new_state = notation_type.get()
            self.notation_state.notation_type.set(new_state)

        tk.OptionMenu(self.subframe, notation_type, *PLUGINS.plugin_names,
                      command=on_change_notation).pack()


class MockProgramState:
    def __init__(self, notation_state: NotationState, note_var, on_modify):
        class GuiState:
            def __init__(self):
                self.tk_current_mode_string = tk.StringVar()

        self.notation_state = notation_state
        self.gui_state = GuiState()
        self.note_var = note_var
        self.on_modify_note = on_modify

    def get_mode_string(self):
        return self.notation_state.mode_name.get()

    def get_current_annotation(self):
        try:
            return json.loads(self.note_var.get())
        except json.decoder.JSONDecodeError:
            return None

    def set_current_annotation(self, content):
        self.note_var.set(json.dumps(content))
        self.on_modify_note()


class InputNoteFrame(BasicFrame):
    def __init__(self, frame, notation_state: NotationState):
        super().__init__(frame, "Note input")
        self.notation_state = notation_state
        self.musical_annotation_frame = None
        self.mock_program_state = None

        self._initialize()

    def _initialize(self):
        frame = tk.Frame(self.subframe)

        lyrics = tk.StringVar(frame)
        note = tk.StringVar(frame)
        line_break = tk.BooleanVar(frame)

        def character_limit(entry_text):
            if len(entry_text.get()) > 1:
                entry_text.set(entry_text.get()[-2:])

        lyrics.trace_add("write", lambda *args: character_limit(lyrics))

        def update_note_and_image(*args):
            idx = self.notation_state.get_current_selection()

            if idx is not None:
                note.set(json.dumps(self.notation_state.music_boxes.get_element(idx).note))
                line_break.set(self.notation_state.music_boxes.get_element(idx).line_break)
                lyrics.set(self.notation_state.music_boxes.get_element(idx).lyrics)  # lyrics must set at last, due to the nature of the lyrics input Entry widget
            else:
                note.set(None)
                line_break.set(False)
                lyrics.set("")
            self.notation_state.display_state.update_image(self.notation_state)
            self.musical_annotation_frame.update_display()

        self.notation_state.display_state._music_listbox.bind('<<ListboxSelect>>', update_note_and_image)

        NotationOptionMenu(frame, self.notation_state).get_frame().grid(row=0, column=0)

        def on_modify_note(*args):
            idx = self.notation_state.get_current_selection()
            if idx is not None:
                self.notation_state.music_boxes.modify_element(idx, MusicBox(lyrics.get(), json.loads(note.get()), line_break.get()))

        self.mock_program_state = MockProgramState(self.notation_state, note, on_modify_note)

        def update_module(*args):
            if self.musical_annotation_frame is not None:
                self.musical_annotation_frame.get_frame().destroy()
            plugin_name = self.notation_state.notation_type.get().lower()
            module = importlib.import_module(f"src.plugins.{plugin_name}")
            if plugin_name.lower() == "jianzipu":
                self.musical_annotation_frame = module.NotationAnnotationFrame(frame, self.mock_program_state,
                                                                               simple=True,
                                                                               started_from_notation_editor=True)
            else:
                self.musical_annotation_frame = module.NotationAnnotationFrame(frame, self.mock_program_state,
                                                                               simple=True)

            self.musical_annotation_frame.set_state(True)
            self.musical_annotation_frame.get_frame().grid(row=1, column=0)

            self.notation_state.get_mode_properties = self.musical_annotation_frame.get_mode_properties
            self.notation_state.set_mode_properties = lambda x: [self.mock_program_state.gui_state.tk_current_mode_string.set(GongdiaoModeList.from_properties(x).name), self.musical_annotation_frame.set_mode_properties(x)]

        self.notation_state.notation_type.trace_add("write", update_module)
        self.notation_state.notation_type.set("Text")

        lyric_linebreak_frame = tk.Frame(frame)
        lyrics_frame = tk.Frame(lyric_linebreak_frame)
        tk.Label(lyrics_frame, text="Lyric").grid(row=0, column=0)
        tk.Entry(lyrics_frame, textvariable=lyrics, width=4, font="Arial 15").grid(row=0, column=1)
        lyrics_frame.grid(row=0, column=0)
        lyrics.trace_add("write", on_modify_note)

        linebreak_frame = tk.Frame(lyric_linebreak_frame)
        tk.Checkbutton(linebreak_frame, text="Line break", variable=line_break, command=on_modify_note).pack()
        linebreak_frame.grid(row=0, column=1)
        lyric_linebreak_frame.grid(row=2, column=0)

        button_frame = tk.Frame(frame)
        button_frame.grid(row=4, column=0)

        frame.pack(padx=5, pady=5)


class NotationOpenCvWindow:
    def __init__(self, window_name, notation_state: NotationState):
        self.window_name = window_name
        self.current_click_coordinates = None
        self.is_clicked = False
        self.point_1 = None
        self.point_2 = None
        self.notation_state = notation_state

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

    def draw_and_handle_clicks(self, image, idx_boxes):
        keypress = cv2.waitKey(1)

        def on_right_click():
            if self.point_1 and self.is_clicked:
                for idx, box in enumerate(idx_boxes):
                    if is_point_in_rectangle(self.point_1, box):
                        self.notation_state.music_boxes.set_cursor(idx)
                self.is_clicked = None

        def on_drag_click():
            if self.point_1 is not None and self.point_2 is not None:
                if is_rectangle_big_enough([self.point_1, self.point_2]):
                    # TODO
                    pass
                self.point_1 = None
                self.point_2 = None
            else:
                self.point_1 = None
                self.point_2 = None

        on_right_click()

        if image is not None:

            ## DEBUG BOXES ##
            #for idx, box in enumerate(idx_boxes):
            #    image_to_draw = cv2.rectangle(image_to_draw, box[0], box[1], (255, 0, 0), 2)

            try:
                box = idx_boxes[self.notation_state.get_current_selection()]
                #rect_image = cv2.rectangle(image_to_draw,  box[0], box[1], (255, 255, 200), -1)
                sub_img = image[box[0][1]:box[1][1], box[0][0]:box[1][0]]
                color = np.ones(sub_img.shape, dtype=np.uint8)
                color[:, :] = (200, 200, 255)
                sub_img = cv2.bitwise_and(color, sub_img)
                image[box[0][1]:box[1][1], box[0][0]:box[1][0]] = sub_img

            except TypeError:
                pass
            cv2.imshow(self.window_name, image)
