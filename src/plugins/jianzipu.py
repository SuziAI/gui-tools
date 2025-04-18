import copy
import dataclasses
import json
import os
import pickle
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.messagebox import askyesno

import PIL
from PIL import ImageTk, Image, ImageChops

from src.auxiliary import BoxType, onedim_cv_to_tkinter_image, open_file_as_tk_image
from src.plugins.suzipu_lvlvpu_gongchepu.notes_to_image import common_notation_to_jianpu, common_notation_to_staff, \
    NotationResources, notation_to_custom
from src.plugins.suzipu_lvlvpu_gongchepu.suzipu_intelligent_assistant import load_model, load_transforms, predict_all
from src.programstate import ProgramState
from src.config import CHINESE_FONT_FILE, NO_KUISCIMA_ANNOTATIONS, FULL_ANNOTATION_NAME
from src.plugins.suzipu_lvlvpu_gongchepu.common import Symbol, SuzipuMelodySymbol, SuzipuAdditionalSymbol, \
    _create_suzipu_images, ModeSelectorFrame, Lvlv, GongcheMelodySymbol


EMPTY_ANNOTATION = {"type": "FULL_JIANZIPU", "content": {"content": ""}}
PLUGIN_NAME = "Jianzipu (structure)"
DISPLAY_NOTATION = True
HAS_MUSICXML = False

def open_images():
    images = {}
    path = "./src/plugins/jianzipu"
    for filename in os.listdir(path):
        if os.path.splitext(filename)[1] == ".png":
            name = os.path.splitext(filename)[0]
            img = Image.open(os.path.join(path, filename))
            images[name] = {}
            images[name]["pil"] = img
            images[name]["tk"] = ImageTk.PhotoImage(image=img)
    images[""] = images["placeholder"]
    return images


RESOURCES = NotationResources()
JIANZIPU_IMAGES = open_images()


def combine_left_right(img1, img2):
    left = img1.resize((img1.size[0] // 2, img1.size[1]))
    right = img2.resize((img2.size[0] // 2, img2.size[1]))
    new_im = Image.new('RGB', (left.size[0] + right.size[0], left.size[1]))
    x_offset = 0
    for im in [left, right]:
        new_im.paste(im, (x_offset, 0))
        x_offset += im.size[0]
    return new_im


def combine_top_bottom(img1, img2):
    top = img1.resize((img1.size[0], img1.size[1] // 2))
    bottom = img2.resize((img2.size[0], img2.size[1] // 2))
    new_im = Image.new('RGB', (top.size[0], top.size[1] + bottom.size[1]))
    y_offset = 0
    for im in [top, bottom]:
        new_im.paste(im, (0, y_offset))
        y_offset += im.size[1]
    return new_im


def combine_left_middle_right(img1, img2, img3):
    left = img1.resize((img1.size[0] // 3, img1.size[1]))
    middle = img2.resize((img2.size[0] // 3, img2.size[1]))
    right = img3.resize((img3.size[0] // 3, img3.size[1]))
    new_im = Image.new('RGB', (left.size[0] + middle.size[0] + right.size[0], left.size[1]))
    x_offset = 0
    for im in [left, middle, right]:
        new_im.paste(im, (x_offset, 0))
        x_offset += im.size[0]
    return new_im


def combine_top_middle_bottom(img1, img2, img3):
    top = img1.resize((img1.size[0], img1.size[1] // 3))
    middle = img2.resize((img2.size[0], img2.size[1] // 3))
    bottom = img3.resize((img3.size[0], img3.size[1] // 3))
    new_im = Image.new('RGB', (top.size[0], top.size[1] + middle.size[1] + bottom.size[1]))
    y_offset = 0
    for im in [top, middle, bottom]:
        new_im.paste(im, (0, y_offset))
        y_offset += im.size[1]
    return new_im


def surround_upper_left(img1, img2):
    outer = img1
    inner = img2.resize((img2.size[0] * 2 // 3, img2.size[1] * 2 // 3))
    new_im = Image.new('RGB', outer.size)
    new_im.paste(outer, (0, 0))
    whitespace = Image.new('RGB', ((outer.size[0] * 2) // 3, (outer.size[1] * 2) // 3), (255, 255, 255))
    new_im.paste(whitespace, (outer.size[0] // 3, outer.size[1] // 3))
    new_inner = Image.new('RGB', outer.size, (255, 255, 255))
    new_inner.paste(inner, (outer.size[0] // 4, outer.size[1] // 4))
    new_im = ImageChops.multiply(new_im, new_inner)
    return new_im


def surround_lower_left(img1, img2):
    outer = img1
    inner = img2.resize((img2.size[0] * 2 // 3, img2.size[1] * 2 // 3))
    new_im = Image.new('RGB', outer.size)
    new_im.paste(outer, (0, 0))
    whitespace = Image.new('RGB', ((outer.size[0] * 2) // 3, (outer.size[1] * 2) // 3), (255, 255, 255))
    new_im.paste(whitespace, (outer.size[0] // 3, 0))
    new_inner = Image.new('RGB', outer.size, (255, 255, 255))
    new_inner.paste(inner, (outer.size[0] // 4, outer.size[1] // 8))
    new_im = ImageChops.multiply(new_im, new_inner)
    return new_im


def surround_upper_right(img1, img2):
    outer = img1
    inner = img2.resize((img2.size[0] * 2 // 3, img2.size[1] * 2 // 3))
    new_im = Image.new('RGB', outer.size)
    new_im.paste(outer, (0, 0))
    whitespace = Image.new('RGB', ((outer.size[0] * 2) // 3, (outer.size[1] * 2) // 3), (255, 255, 255))
    new_im.paste(whitespace, (0, outer.size[1] // 3))
    new_inner = Image.new('RGB', outer.size, (255, 255, 255))
    new_inner.paste(inner, (outer.size[0] // 8, outer.size[1] // 4))
    new_im = ImageChops.multiply(new_im, new_inner)
    return new_im


ACTION_LIST = [
            {"symbol": "⿰", "children": ["Left", "Right"], "combine": combine_left_right},
            {"symbol": "⿱", "children": ["Top", "Bottom"], "combine": combine_top_bottom},
            {"symbol": "⿲", "children": ["Left", "Middle", "Right"], "combine": combine_left_middle_right},
            {"symbol": "⿳", "children": ["Top", "Middle", "Bottom"], "combine": combine_top_middle_bottom},
            {"symbol": "⿸", "children": ["Outer", "Inner"], "combine": surround_upper_left},
            {"symbol": "⿺", "children": ["Outer", "Inner"], "combine": surround_lower_left},
            {"symbol": "⿹", "children": ["Outer", "Inner"], "combine": surround_upper_right},
            # {"symbol": "⿶", "children": ["Outer", "Inner"]},
            # {"symbol": "⿷", "children": ["Outer", "Inner"]},
            # {"symbol": "⿵", "children": ["Outer", "Inner"]},
            # {"symbol": "⿴", "children": ["Outer", "Inner"]},
            # {"symbol": "⿻", "children": ["Topleft", "Bottomright"]}
        ]


def notation_to_own(mode, music_list, lyrics_list, line_break_idxs, fingering, return_boxes=False, is_vertical=False):
    def get_full_jianzipu_image(note):
        children = []
        try:
            children = note["children"]
        except KeyError:
            pass

        content = note["content"]
        if len(children):  # child is no leaf node
            for action in ACTION_LIST:
                if action["symbol"] == content:
                    break
            return action["combine"](*[get_full_jianzipu_image(child) for child in children])
        else:
            return JIANZIPU_IMAGES[str(content)]["pil"]

    def get_left_hand_image(note):
        copy_note = copy.deepcopy(note)
        if len(copy_note) <= 4:
            for idx in range(4-len(copy_note)):
                copy_note.append("none")
            return combine_left_right(combine_top_bottom(JIANZIPU_IMAGES[str(copy_note[2])]["pil"], JIANZIPU_IMAGES[str(copy_note[3])]["pil"]), combine_top_bottom(JIANZIPU_IMAGES[str(copy_note[0])]["pil"], JIANZIPU_IMAGES[str(copy_note[1])]["pil"]))
        else:
            raise ValueError("Error: Left hand note may only contain up to four symbols.")

    def get_string_number_image(note):
        return JIANZIPU_IMAGES[str(note)]["pil"]

    def get_image(note):
        if "type" not in note:
            note = EMPTY_ANNOTATION

        if note["type"] == JianzipuSymbolType.FULL_JIANZIPU:
            return get_full_jianzipu_image(note["content"])
        elif note["type"] == JianzipuSymbolType.LEFT_HAND:
            return get_left_hand_image(note["content"])
        elif note["type"] == JianzipuSymbolType.STRING_NUMBER:
            return get_string_number_image(note["content"])
        else:
            return get_full_jianzipu_image(EMPTY_ANNOTATION)

    custom_notation_image_list = [get_image(note) for note in music_list]

    return notation_to_custom(
                    RESOURCES.small_font,
                    custom_notation_image_list, lyrics_list,
                    line_break_idxs,
                    return_boxes,
                    is_vertical)


class FullJianzipuAnnotationFrame:
    def __init__(self, window_handle, annotation_images, program_state, update_thumbnail, update_annotation, keys, started_from_notation_editor):
        self.window_handle = window_handle
        self.program_state = program_state
        self.parent_node = None
        self.musical_var = None
        self.frame = tk.Frame(window_handle)
        self.update_thumbnail = lambda: update_thumbnail(self.get_node_image(self.parent_node))
        self.annotation_images = annotation_images
        self.update_annotation = update_annotation

        self.started_from_notation_editor = started_from_notation_editor

        self.keys = keys

        self.state = False

        self._widgets = []
        self.annotation_widgets = []

        self.actions_list = ACTION_LIST

        self._create_frame()

    def get_action_from_symbol(self, symbol):
        for action in self.actions_list:
            if action["symbol"] == symbol:
                return action
        return None

    def _create_frame(self):
        display_treeview_frame = tk.Frame(self.frame)

        treeview_frame = tk.Frame(display_treeview_frame)
        self.musical_var = ttk.Treeview(treeview_frame, selectmode="browse")

        def update_annotation_buttons(*args):
            for widget in self.annotation_widgets:
                if self.state is True and len(self.musical_var.selection()) and len(self.musical_var.get_children(self.musical_var.selection()[0])) == 0:
                    widget.config(state="normal")
                else:
                    widget.config(state="disabled")

        self.musical_var.bind('<<TreeviewSelect>>', update_annotation_buttons)
        self.musical_var.pack(side="left")
        vsb = ttk.Scrollbar(treeview_frame, orient="vertical", command=self.musical_var.yview)
        self.musical_var.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        treeview_frame.pack(side="right")

        display_treeview_frame.grid(row=0)

        self.parent_node = self.musical_var.insert("", tk.END, text="⬚", values=[""])

        actions_frame = tk.Frame(self.frame)

        for idx, action in enumerate(self.actions_list):
            curr_button = tk.Button(actions_frame, text=action["symbol"], command=self.replace_current_node(action), state="disabled")
            curr_button.grid(row=0, column=idx)
            self._widgets.append(curr_button)
        actions_frame.grid(row=1)

        annotation_buttons_frame = tk.Frame(self.frame)
        others_frame = tk.Frame(self.frame)
        annotation_var = tk.StringVar()
        display_node_annotation = tk.BooleanVar(others_frame, value=False)

        def show_or_hide_annotation_frame():
            if display_node_annotation.get():
                annotation_buttons_frame.grid(row=3)
            else:
                annotation_buttons_frame.grid_forget()

        def on_quick_fill():
            exit_save_var, text_variable = exec_quick_fill_window(self.program_state.gui_state.tk_current_boxtype,
                                                                  self.program_state.gui_state.tk_num_all_boxes_of_current_type)
            if exit_save_var:
                self.program_state.fill_all_boxes_of_current_type(json.loads(text_variable))

        display_node_annotation_checkbox = tk.Checkbutton(others_frame, text="Display Node Annotation", variable=display_node_annotation, command=show_or_hide_annotation_frame)
        clear_button = tk.Button(others_frame, text="Clear", command=self.clear_tree, state="disabled")
        clear_button.grid(row=0, column=0)
        quick_fill_button = tk.Button(others_frame, text="Quick Fill...", command=on_quick_fill, state="disabled")
        quick_fill_button.grid(row=0, column=1)
        display_node_annotation_checkbox.grid(row=0, column=2)
        others_frame.grid(row=2)

        outer_col = 0
        for label in self.keys.keys():
            current_frame = tk.LabelFrame(annotation_buttons_frame, text=label)
            row_idx = 0
            col_idx = 0
            for key in self.keys[label]:
                if key is None:
                    row_idx = 0
                    col_idx += 1
                    continue
                widget = tk.Radiobutton(current_frame, image=self.annotation_images[key]["tk"], variable=annotation_var,
                                        value=key, indicator=0, state="disabled",
                                        command=self.update_treeview(key))
                widget.grid(row=row_idx, column=col_idx)
                self.annotation_widgets.append(widget)
                row_idx += 1
            current_frame.grid(row=0, column=outer_col)
            outer_col += 1

        self._widgets += [clear_button, quick_fill_button]

    def get_frame(self):
        return self.frame

    def update_treeview(self, annotation):
        def inner():
            selection = self.musical_var.selection()
            self.musical_var.item(selection, values=[annotation])
            self.update_thumbnail()
            self.update_annotation(self.get_full_dict())

        return inner

    def open_children(self, parent):
        self.musical_var.item(parent, open=True)
        for child in self.musical_var.get_children(parent):
            self.open_children(child)

    def get_dict(self, node):
        total_values = {}
        node_values = self.musical_var.item(node)["values"]
        children = self.musical_var.get_children(node)
        total_values["content"] = node_values[0]
        if len(children):  # child is no leaf node
            total_values["children"] = [self.get_dict(child) for child in children]
        return total_values

    def get_full_dict(self):
        return {"type": JianzipuSymbolType.FULL_JIANZIPU, "content": self.get_dict(self.parent_node)}

    def get_list(self, node):
        total_values = []
        node_values = self.musical_var.item(node)["values"]
        children = self.musical_var.get_children(node)
        total_values.append(node_values[0])
        total_values += [self.get_list(child) for child in children]
        return total_values if len(total_values) > 1 else total_values[0]

    def print_dict(self):
        print(self.get_dict(self.parent_node))

    def print_list(self):
        print(self.get_list(self.parent_node))

    def get_node_image(self, node):
        children = self.musical_var.get_children(node)
        content = str(self.musical_var.item(node)["values"][0])
        if len(children):  # child is no leaf node
            for action in self.actions_list:
                if action["symbol"] == content:
                    break
            return action["combine"](*[self.get_node_image(child) for child in children])
        else:
            return self.annotation_images[content]["pil"]

    def replace_current_node(self, action):
        def inner():
            selection = self.musical_var.selection()
            if len(selection) == 0:
                selection = self.parent_node
            else:
                selection = selection[0]
            self.replace_node(action, selection)
            self.update_annotation(self.get_full_dict())

        return inner

    def replace_node(self, action, node):
        symbols_string = "".join([action["symbol"] for action in self.actions_list])

        if node == self.parent_node:
            self.musical_var.item(node, text=f"{action['symbol']}", values=[action["symbol"]])
        else:
            selection_text = self.musical_var.item(node)["text"]
            position = selection_text.strip(symbols_string).strip()
            self.musical_var.item(node, text=f"{position} {action['symbol']}", values=[action["symbol"]])

        self.musical_var.delete(*self.musical_var.get_children(node))

        for child in action["children"]:
            self.musical_var.insert(node, tk.END, text=f"{child}", values=[""])
        self.open_children("")
        self.update_thumbnail()

    def build_tree_from_dict(self, dictionary):
        if "content" not in dictionary:
            dictionary = EMPTY_ANNOTATION
        def build_node(node, subdict):
            action = self.get_action_from_symbol(subdict["content"])
            if action is not None:
                self.replace_node(action, node)
                children = self.musical_var.get_children(node)
                for idx, child in enumerate(children):
                    build_node(child, subdict["children"][idx])
            else:
                self.musical_var.item(node, values=[str(subdict["content"])])

        build_node(self.parent_node, dictionary["content"])

        if not self.started_from_notation_editor:
            self.update_annotation(self.get_full_dict())

    def clear_tree(self, *args):
        self.musical_var.delete(*self.musical_var.get_children())
        self.parent_node = self.musical_var.insert("", tk.END, text="⬚", values=[""])
        self.update_thumbnail()

        if not self.started_from_notation_editor:
            self.update_annotation(self.get_full_dict())

    def set_from_annotation(self, annotation):
        self.clear_tree()
        if annotation is not None:
            self.build_tree_from_dict(annotation)

    def set_state(self, boolean):
        self.state = boolean
        for widget in self._widgets:
            widget.config(state="normal" if boolean else "disabled")


class StringNumberAnnotationFrame:
    def __init__(self, window_handle, annotation_images, program_state, update_thumbnail, update_annotation, keys):
        self.window_handle = window_handle
        self.program_state = program_state
        self.parent_node = None
        self.musical_var = tk.StringVar(self.window_handle)
        self.frame = tk.Frame(window_handle)
        self.update_thumbnail = lambda: update_thumbnail(self.get_image())
        self.annotation_images = annotation_images
        self.update_annotation = lambda: [update_annotation({"type": JianzipuSymbolType.STRING_NUMBER, "content": self.musical_var.get()}), update_thumbnail(self.get_image())]

        self.keys = keys
        self._widgets = []

        self._create_frame()

    def _create_frame(self):
        outer_col = 0
        for label in self.keys.keys():
            current_frame = tk.LabelFrame(self.frame, text=label)
            row_idx = 0
            col_idx = 0
            for key in self.keys[label]:
                if key is None:
                    col_idx += 1
                    row_idx = 0
                    continue
                widget = tk.Radiobutton(current_frame, image=self.annotation_images[key]["tk"], variable=self.musical_var,
                                        value=key, indicator=0, state="disabled",
                                        command=self.update_annotation)
                widget.grid(row=row_idx, column=col_idx)
                row_idx += 1
                self._widgets.append(widget)
            current_frame.grid(row=0, column=outer_col)
            outer_col += 1

    def set_from_annotation(self, annotation):
        if annotation is not None:
            self.musical_var.set(annotation["content"])

    def get_image(self):
        return self.annotation_images[self.musical_var.get()]["pil"]

    def get_frame(self):
        return self.frame

    def set_state(self, boolean):
        for widget in self._widgets:
            widget.config(state="normal" if boolean else "disabled")


class LeftHandAnnotationFrame:
    def __init__(self, window_handle, annotation_images, program_state, update_thumbnail, update_annotation, keys, started_from_notation_editor):
        self.window_handle = window_handle
        self.program_state = program_state
        self.parent_node = None
        self.musical_var = None
        self.frame = tk.Frame(window_handle)
        self.update_thumbnail = lambda: update_thumbnail(self.get_image())
        self.annotation_images = annotation_images
        self.update_annotation = update_annotation
        self.started_from_notation_editor = started_from_notation_editor

        self.keys = keys

        self._widgets = []

        self._create_frame()

    def _create_frame(self):
        treeview_frame = tk.Frame(self.frame)
        style = ttk.Style()
        style.configure("mystyle.Treeview", rowheight=30)  # Modify the font of the body
        self.musical_var = ttk.Treeview(treeview_frame, selectmode="browse", style="mystyle.Treeview", height=6)
        self.musical_var.pack()
        treeview_frame.pack()

        others_frame = tk.Frame(self.frame)
        delete_button = tk.Button(others_frame, text="Delete Entry", command=self.delete_selection, state="disabled")
        clear_button = tk.Button(others_frame, text="Clear List", command=self.clear_tree, state="disabled")
        delete_button.grid(row=0, column=0)
        clear_button.grid(row=0, column=1)
        self._widgets += [delete_button, clear_button]
        others_frame.pack()

        buttons_frame = tk.Frame(self.frame)

        outer_col = 0
        for label in self.keys.keys():
            current_frame = tk.LabelFrame(buttons_frame, text=label)
            row_idx = 0
            col_idx = 0
            for key in self.keys[label]:
                if key is None:
                    row_idx = 0
                    col_idx += 1
                    continue
                widget = tk.Radiobutton(current_frame, image=self.annotation_images[key]["tk"],
                                        value=key, indicator=0, state="disabled",
                                        command=self.insert_after_selection(key))
                widget.grid(row=row_idx, column=col_idx)
                self._widgets.append(widget)
                row_idx += 1
            current_frame.grid(row=0, column=outer_col)
            outer_col += 1
        buttons_frame.pack()

    def insert_after_selection(self, key):
        def inner():
            selection = self.musical_var.selection()
            if len(selection) == 0:
                idx = "end"
            else:
                idx = self.musical_var.index(selection)
            self.musical_var.insert("", idx, text=key, image=self.annotation_images[key]["tk"])
            self.update_annotation(self.get_full_dict())
        return inner

    def delete_selection(self):
        selection = self.musical_var.selection()
        if len(selection) == 0:
            selection = self.musical_var.get_children("")[-1]
        self.musical_var.delete(selection)
        self.update_annotation(self.get_full_dict())

    def get_dict(self):
        values = []
        children = self.musical_var.get_children("")
        for child in children:
            values.append(str(self.musical_var.item(child)["text"]))
        return values

    def get_full_dict(self):
        return {"type": JianzipuSymbolType.LEFT_HAND, "content": self.get_dict()}

    def clear_tree(self, *args):
        self.musical_var.delete(*self.musical_var.get_children())
        self.update_thumbnail()

        if not self.started_from_notation_editor:
            self.update_annotation(self.get_full_dict())

    def set_from_annotation(self, annotation):
        self.clear_tree()
        if annotation is not None and "content" in annotation:
            for item in annotation["content"]:
                try:
                    self.musical_var.insert("", "end", image=self.annotation_images[item]["tk"], text=item)
                    if not self.started_from_notation_editor:
                        self.update_annotation(self.get_full_dict())
                except KeyError:
                    pass

    def get_image(self):
        return self.annotation_images[""]["pil"]

    def get_frame(self):
        return self.frame

    def set_state(self, boolean):
        for widget in self._widgets:
            widget.config(state="normal" if boolean else "disabled")


@dataclasses.dataclass
class JianzipuSymbolType:
    FULL_JIANZIPU: str = "FULL_JIANZIPU"
    STRING_NUMBER: str = "STRING_NUMBER"
    LEFT_HAND: str = "LEFT_HAND"


def exec_quick_fill_window(annotation_type_var, max_length_var):
    quick_fill_window = tk.Toplevel()

    exit_save_var = tk.BooleanVar()
    exit_save_var.set(False)
    def on_destroy_save_changes():
        exit_save_var.set(True)
        quick_fill_window.destroy()

    annotation_type = annotation_type_var.get()

    quick_fill_window.title(f"Quick Fill {annotation_type}")

    text_variable = tk.StringVar(quick_fill_window)
    text_variable.set("")

    left_character_string = tk.StringVar(quick_fill_window)
    left_character_string.set("")
    ok_button = tk.Button(quick_fill_window, text="OK", command=on_destroy_save_changes, state="normal")

    tk.Entry(quick_fill_window, font=CHINESE_FONT_FILE,
             textvariable=text_variable).pack()
    tk.Label(quick_fill_window, textvariable=left_character_string).pack()
    ok_button.pack()

    quick_fill_window.wait_window()

    return exit_save_var.get(), text_variable.get()


class NotationAnnotationFrame:
    def __init__(self, window_handle, program_state, simple=False, started_from_notation_editor=False):
        self.window_handle = window_handle
        self.program_state = program_state
        self.display_image = None
        self.simple = simple

        self.started_from_notation_editor = started_from_notation_editor

        self.frame = tk.Frame(self.window_handle)

        with open("./src/plugins/jianzipu/gui_config.json", "r") as file:
            self.config = json.load(file)

        self.mode_selector = None

        self.selection_variable = tk.StringVar(self.frame, "Full")
        self._widgets = []
        self.current_img = None
        self.annotation_images = JIANZIPU_IMAGES
        self.annotation_widgets = []

        def get_reference_images():
            with open("./src/plugins/suzipu_lvlvpu_gongchepu/suzi_lvlv_jianzi_references.pkl", "rb") as file_handle:
                obj = pickle.load(file_handle)
                for key in obj.keys():
                    for key2 in obj[key].keys():
                        obj[key][key2] = onedim_cv_to_tkinter_image(obj[key][key2])
                return obj

        self.reference_images = get_reference_images()
        self.canvas = None
        self._image = None
        self.no_annotations_image = open_file_as_tk_image(NO_KUISCIMA_ANNOTATIONS)

        self._create_frame()

    def _create_frame(self):
        annotation_selection_frame = tk.Frame(self.frame)

        def on_intelligent():
            intelligent_assistant_window = tk.Toplevel(self.frame)
            intelligent_assistant_window.title(f"{FULL_ANNOTATION_NAME} - Jianzipu Intelligent Assistant")

            canvas_frame = tk.LabelFrame(intelligent_assistant_window, text="KuiSCIMA Instances With Same Annotation")
            self.canvas = tk.Canvas(canvas_frame, relief="sunken", state="disabled")
            vbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
            vbar.pack(side=tk.RIGHT, fill=tk.BOTH)
            vbar.config(command=self.canvas.yview)
            self.canvas.config(yscrollcommand=vbar.set)
            self.canvas.pack(padx=5, pady=5)

            def onFrameConfigure(event):
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))

            canvas_frame.bind("<Configure>", onFrameConfigure)
            canvas_frame.pack(padx=5, pady=5)

            self.update_display()

        intelligent_frame = tk.Frame(annotation_selection_frame)
        intelligent_button = tk.Button(intelligent_frame, text="Intelligent Assistant...", command=on_intelligent,
                                       state="disabled")
        intelligent_button.pack()
        intelligent_frame.grid(row=0, column=0)

        jzp_button = tk.Radiobutton(annotation_selection_frame, text="Full Jianzipu", indicator=0, state="disabled",
                                    value=JianzipuSymbolType.FULL_JIANZIPU, variable=self.selection_variable,
                                    command=lambda: self._change_frame(JianzipuSymbolType.FULL_JIANZIPU))
        jzp_button.grid(row=0, column=1)
        sn_button = tk.Radiobutton(annotation_selection_frame, text="String Number", indicator=0, state="disabled",
                                   value=JianzipuSymbolType.STRING_NUMBER, variable=self.selection_variable,
                                   command=lambda: self._change_frame(JianzipuSymbolType.STRING_NUMBER))
        sn_button.grid(row=0, column=2)
        lh_button = tk.Radiobutton(annotation_selection_frame, text="Left Hand", indicator=0, state="disabled",
                                   value=JianzipuSymbolType.LEFT_HAND, variable=self.selection_variable,
                                   command=lambda: self._change_frame(JianzipuSymbolType.LEFT_HAND))
        lh_button.grid(row=0, column=3)

        notation_subframe = tk.Frame(self.frame)
        display_frame = tk.Frame(notation_subframe)
        self.display_image = tk.Label(display_frame, image=self.annotation_images["none"]["tk"], relief="sunken", state="disabled")
        self.display_image.pack(side="left", padx=10)
        self.full_jianzipu_frame = FullJianzipuAnnotationFrame(display_frame, self.annotation_images, self.program_state, self.update_thumbnail, self.update_annotation, self.config["FullJianzipuAnnotation"], started_from_notation_editor=self.started_from_notation_editor)
        self.string_number_annotation_frame = StringNumberAnnotationFrame(display_frame, self.annotation_images, self.program_state, self.update_thumbnail, self.update_annotation, self.config["StringNumberAnnotation"])
        self.left_hand_annotation_frame = LeftHandAnnotationFrame(display_frame, self.annotation_images, self.program_state, self.update_thumbnail, self.update_annotation, self.config["LeftHandAnnotation"], started_from_notation_editor=self.started_from_notation_editor)

        self.current_frame = self.full_jianzipu_frame
        self.current_frame.get_frame().pack(side="right", padx=10)

        display_frame.pack(side="left", padx=10)

        annotation_selection_frame.pack(side="top")
        notation_subframe.pack(side="bottom")

        self._widgets = [self.display_image, intelligent_button, jzp_button, sn_button, lh_button]

    def _change_frame(self, id):
        if id == JianzipuSymbolType.FULL_JIANZIPU:
            new_frame = self.full_jianzipu_frame
        elif id == JianzipuSymbolType.STRING_NUMBER:
            new_frame = self.string_number_annotation_frame
        elif id == JianzipuSymbolType.LEFT_HAND:
            new_frame = self.left_hand_annotation_frame

        self.selection_variable.set(id)
        self.current_frame.get_frame().pack_forget()
        self.current_frame = new_frame
        self.current_frame.get_frame().pack(side="right", padx=10)
        self.current_frame.set_from_annotation(self.program_state.get_current_annotation())

    def update_thumbnail(self, image):
        self.current_img = ImageTk.PhotoImage(image=image)
        self.display_image.configure(image=self.current_img)

    def get_frame(self):
        return self.frame

    def update_display(self):
        annotation = self.program_state.get_current_annotation()

        if self.canvas:
            try:
                self.canvas.delete('all')
                self._image = self.reference_images["Jianzipu"][str(annotation)]
                self.canvas.yview_moveto(0)
            except Exception as e:
                print(e)
                self._image = self.no_annotations_image
            image_on_canvas = self.canvas.create_image(0, 0, image=self._image, anchor="nw")
            self.canvas.config(width=600,
                               height=500)

        try:
            self._change_frame(annotation["type"])
        except (KeyError, TypeError) as e:
            self._change_frame("FULL_JIANZIPU")

        self.current_frame.set_from_annotation(annotation)
        self.current_frame.update_thumbnail()

    def update_annotation(self, annotation):
        self.program_state.set_current_annotation(annotation)

        if self.canvas:
            try:
                self.canvas.delete('all')
                self._image = self.reference_images["Jianzipu"][str(annotation)]
                self.canvas.yview_moveto(0)
            except Exception as e:
                print(e)
                self._image = self.no_annotations_image
            image_on_canvas = self.canvas.create_image(0, 0, image=self._image, anchor="nw")
            self.canvas.config(width=600,
                               height=500)

    def set_state(self, boolean):
        if boolean:
            state = "normal"
        else:
            state = "disabled"

        for widget in self._widgets:
            widget.config(state=state)
        self.full_jianzipu_frame.set_state(boolean)
        self.string_number_annotation_frame.set_state(boolean)
        self.left_hand_annotation_frame.set_state(boolean)
        #self.mode_selector.set_state(boolean)

    def set_mode_properties(self, props: dict):
        pass
        #self.mode_selector.set_properties(props)

    def get_mode_properties(self):
        pass
        #return self.mode_selector.get_properties()