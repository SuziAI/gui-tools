import dataclasses
import tkinter as tk
from tkinter import filedialog, messagebox

import PIL
import chinese_converter
from PIL import ImageTk

from src.auxiliary import SetInt, SelectionMode, BoxProperty, get_class_variables, bgr_to_tkinter, box_property_to_color, \
    open_file_as_tk_image, _create_suzipu_images
from src.modes import GongdiaoMode, GongdiaoModeList, get_tone_inventory, Lvlv, GongdiaoStep, ModeProperties
from src.config import JIANPU_BUTTON_IMAGE, FIVELINE_BUTTON_IMAGE
from src.suzipu import SuzipuMelodySymbol, SuzipuAdditionalSymbol, suzipu_to_info, Symbol, GongcheMelodySymbol
from src.notes_to_image import Fingering


def exec_path_select_window(image_dir_text="", output_dir_text="", weight_file_text=""):
    path_select_window = tk.Tk()
    path_select_window.title("Suzipu Musical Annotation Tool - Select Paths")

    image_dir = tk.StringVar();
    image_dir.set(image_dir_text)
    output_dir = tk.StringVar();
    output_dir.set(output_dir_text)
    weight_file = tk.StringVar();
    weight_file.set(weight_file_text)

    def update_button_state():
        if image_dir.get() and output_dir.get():  #and weight_file.get():
            b_continue.config(state="normal")

    def select_image_dir():
        dir_text = filedialog.askdirectory(
            title='Open the image_to_draw directory',
            initialdir='.',
            mustexist=True
        )
        image_dir.set(dir_text)
        update_button_state()

    def select_output_dir():
        dir_text = filedialog.askdirectory(
            title='Open the output directory',
            initialdir='.',
            mustexist=True
        )
        output_dir.set(dir_text)
        update_button_state()

    def select_weight_file():
        filetypes = (
            ('recommended files', '*.pth.tar'),
            ('All files', '*.*')
        )
        dir_text = filedialog.askopenfilename(
            title='Open the model weight file',
            initialdir='.',
            filetypes=filetypes
        )
        weight_file.set(dir_text)
        update_button_state()

    images_label = tk.Label(path_select_window, text="Select Image Directory (containing the Chinese text images)")
    images_dirbox = tk.Label(path_select_window, height=1, width=100, textvariable=image_dir, relief="sunken")
    images_open = tk.Button(path_select_window, text="Open...", command=select_image_dir)

    output_label = tk.Label(path_select_window, text="Select Output Directory (default directory for saving the files)")
    output_dirbox = tk.Label(path_select_window, height=1, width=100, textvariable=output_dir, relief="sunken")
    output_open = tk.Button(path_select_window, text="Open...", command=select_output_dir)

    weights_label = tk.Label(path_select_window, text="Select model weights file (must be *.pth.tar)")
    weights_dirbox = tk.Label(path_select_window, height=1, width=100, textvariable=weight_file, relief="sunken")
    weights_open = tk.Button(path_select_window, text="Open...", command=select_weight_file)

    # Create an Exit button.
    b_continue = tk.Button(path_select_window, text="Continue",
                           command=path_select_window.destroy, state="disabled")

    update_button_state()

    images_label.pack()
    images_dirbox.pack()
    images_open.pack(pady=(0, 20))
    output_label.pack()
    output_dirbox.pack()
    output_open.pack(pady=(0, 20))
    #weights_label.pack()
    #weights_dirbox.pack()
    #weights_open.pack(pady=(0, 20))
    b_continue.pack()

    path_select_window.mainloop()

    return image_dir.get(), output_dir.get(), weight_file.get()


def on_closing(window_handle):
    def close():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            window_handle.destroy()
            exit()

    return close


class PreviousNextFrame:
    def __init__(self, window_handle, display_variable, on_previous=lambda: None, on_next=lambda: None):
        self.window_handle = window_handle
        self.display_variable = display_variable
        self.on_previous = on_previous
        self.on_next = on_next
        self.frame = tk.LabelFrame(self.window_handle, text="Base image_to_draw")

        self._create_frame()

    def _create_frame(self):
        internal_frame = tk.Frame(self.frame)
        previous_button = tk.Button(internal_frame, text="<< Previous", command=self.on_previous)
        base_image_path_display = tk.Label(internal_frame, height=1, width=50, textvariable=self.display_variable,
                                              relief="sunken")
        next_button = tk.Button(internal_frame, text="Next >>", command=self.on_next)

        previous_button.grid(row=0, column=0)
        base_image_path_display.grid(row=0, column=1)
        next_button.grid(row=0, column=2)

        internal_frame.pack(padx=10, pady=10)

    def get_frame(self):
        return self.frame


class IncrementDecrementFrame:
    def __init__(self, window_handle, counter: SetInt, on_change=lambda: None):
        self.window_handle = window_handle
        self.frame = tk.Frame(self.window_handle)
        self.counter = counter
        self.internal_counter = tk.IntVar()
        self.on_change = on_change

        self.internal_counter.set(1)
        self._create_frame()

    def set_counter(self, number):
        self.internal_counter.set(number)

    def _on_append_modify(self, increment_or_decrement: str):
        if increment_or_decrement == "increment":
            change = self.counter.increment
        elif increment_or_decrement == "decrement":
            change = self.counter.decrement
        else:
            raise Exception(f"Invalid value, expected 'increment' or 'decrement', but got {increment_or_decrement}")

        def func():
            change()
            self.internal_counter.set(self.counter.get())
            self.on_change()

        return func

    def _create_frame(self):
        append_right_decrement = tk.Button(self.frame, text="-", command=self._on_append_modify("decrement"))
        append_right_display = tk.Label(self.frame, height=1, width=2, textvariable=self.internal_counter,
                                        relief="sunken")
        append_right_increment = tk.Button(self.frame, text="+", command=self._on_append_modify("increment"))

        append_right_decrement.grid(row=0, column=0)
        append_right_display.grid(row=0, column=1)
        append_right_increment.grid(row=0, column=2)

    def get_frame(self):
        return self.frame


class SelectionFrame:
    def __init__(self, window_handle, selectionmode_var: tk.StringVar, boxtype_var: tk.StringVar,
                 on_click_annotate=lambda: None, on_change_mode_selection=lambda: None,
                 on_change_box_type_selection=lambda: None):
        self.window_handle = window_handle
        self.frame = tk.LabelFrame(self.window_handle, text="Box Manipulation")
        self.selectionmode_var = selectionmode_var
        self.boxtype_var = boxtype_var
        self.on_click_annotate = on_click_annotate
        self.on_change_mode_selection = on_change_mode_selection
        self.on_change_box_type_selection = on_change_box_type_selection
        self.is_active = False

        self._create_frame()

    def _create_frame(self):
        frame1 = tk.Frame(self.frame)
        frame2 = tk.Frame(self.frame)

        boxtype_buttons = []
        for boxtype_var in dataclasses.astuple(BoxProperty()):
            boxtype_buttons.append(tk.Radiobutton(frame2, text=boxtype_var, variable=self.boxtype_var,
                                                  value=boxtype_var, indicator=0, state="disabled",
                                                  bg=bgr_to_tkinter(box_property_to_color(boxtype_var)),
                                                  command=self.on_change_box_type_selection))

        def _on_change_selection_mode():
            self.is_active = self.selectionmode_var.get() in [SelectionMode.CREATE, SelectionMode.MARK,
                                                              SelectionMode.ANNOTATE]
            state = "normal" if self.is_active else "disabled"

            for boxtype_button_element in boxtype_buttons:
                boxtype_button_element.config(state=state)
            self.on_change_mode_selection()

        for idx, selection_mode in enumerate(get_class_variables(SelectionMode)):
            if selection_mode == SelectionMode.ANNOTATE:
                command = lambda: [self.on_click_annotate(), _on_change_selection_mode()]
            else:
                command = _on_change_selection_mode
            tk.Radiobutton(frame1, text=selection_mode, variable=self.selectionmode_var,
                           value=selection_mode, indicator=0, command=command).grid(row=0, column=idx)

        for idx, boxtype_button in enumerate(boxtype_buttons):
            boxtype_button.grid(row=0, column=idx)

        frame1.grid(row=0, column=0, pady=5, padx=10)
        frame2.grid(row=1, column=0, pady=5, padx=10)

    def get_frame(self):
        return self.frame


class SaveLoadFrame:
    def __init__(self, window_handle, on_save_image=lambda: None, on_save=lambda: None, on_save_text=lambda: None, on_load=lambda: None):
        self.window_handle = window_handle
        self.frame = tk.Frame(self.window_handle)
        self.on_save_image = on_save_image
        self.on_save = on_save
        self.on_load = on_load
        self.on_save_text = on_save_text

        self._create_frame()

    def _create_frame(self):
        tk.Button(self.frame, text="Save", command=self.on_save).grid(row=0, column=0)
        tk.Button(self.frame, text="Load", command=self.on_load).grid(row=0, column=1)
        tk.Label(self.frame, text="").grid(row=0, column=2, padx=10)
        tk.Button(self.frame, text="Export whole Image", command=self.on_save_image).grid(row=0, column=3)
        tk.Button(self.frame, text="Export as Text", command=self.on_save_text).grid(row=0, column=4)

    def get_frame(self):
        return self.frame


class DisplayNotesFrame:
    def __init__(self, window_handle, on_save_notation=lambda: None, on_save_musicxml=lambda: None):
        self.window_handle = window_handle
        self.on_save_notation = on_save_notation
        self.on_save_musicxml = on_save_musicxml
        self.frame = tk.LabelFrame(self.window_handle, text="Modern Notation")
        self._image = None
        self.label = tk.Label(self.frame, image=None, relief="sunken", state="disabled")
        self.var_is_jianpu = tk.BooleanVar()
        self.var_is_jianpu.set(True)

        self.transposition_string = tk.StringVar()
        self.transposition_string.set(Fingering.ALL_CLOSED_AS_1.name)

        self.widgets = [self.label]

        self.jianpu_image = open_file_as_tk_image(JIANPU_BUTTON_IMAGE)
        self.fiveline_image = open_file_as_tk_image(FIVELINE_BUTTON_IMAGE)

        self._create_frame()

    def _create_frame(self):
        fingering_names = [fingering.name for fingering in dataclasses.astuple(Fingering())]

        selection_frame = tk.Frame(self.frame)
        jianpu_button = tk.Radiobutton(selection_frame, image=self.jianpu_image, variable=self.var_is_jianpu,
                       value=True,
                       indicator=0, state="disabled")
        fiveline_button = tk.Radiobutton(selection_frame, image=self.fiveline_image, variable=self.var_is_jianpu,
                       value=False,
                       indicator=0, state="disabled")
        transposition_menu = tk.OptionMenu(selection_frame, self.transposition_string, *fingering_names)
        save_notation_to_file_button = tk.Button(selection_frame, text="Export Notation as Image", command=self.on_save_notation)
        save_notation_to_musicxml_button = tk.Button(selection_frame, text="Export Notation as MusicXML",
                                                 command=self.on_save_musicxml)

        jianpu_button.grid(row=0, column=0)
        fiveline_button.grid(row=0, column=1)
        transposition_menu.grid(row=0, column=2)
        save_notation_to_file_button.grid(row=0, column=4)
        save_notation_to_musicxml_button.grid(row=0, column=5)

        self.widgets += [jianpu_button, fiveline_button, transposition_menu, save_notation_to_file_button, save_notation_to_musicxml_button]

        selection_frame.pack()
        self.label.pack(padx=10, pady=10)

    def set_state(self, boolean):
        state = "disabled"
        if boolean:
            state = "normal"

        for widget in self.widgets:
            widget.config(state=state)

    def set_image(self, image):
        self._image = image
        self.label.config(image=self._image)

    def get_frame(self):
        return self.frame

    def is_jianpu(self):
        return self.var_is_jianpu.get()

    def get_transposition(self):
        return Fingering.from_string(self.transposition_string.get())


class StatisticsFrame:
    def __init__(self, window_handle):
        self.window_handle = window_handle
        self.frame = tk.LabelFrame(self.window_handle, text="Statistics")
        self.label = tk.Label(self.frame, image=None, relief="sunken", state="disabled")

        self.button_img_dictionary, self.statistics_text_var_dictionary = self._create_dicts()

        self.widgets = [self.label]

        self._create_frame()

    @classmethod
    def _create_dicts(cls):
        button_img_dictionary = {}
        statistics_text_var_dictionary = {}
        for melody_var in dataclasses.astuple(SuzipuMelodySymbol()):
            button_img_dictionary[melody_var] = open_file_as_tk_image(suzipu_to_info(melody_var).button_image_filename)
            statistics_text_var_dictionary[melody_var] = tk.StringVar()
        for additional_var in dataclasses.astuple(SuzipuAdditionalSymbol()):
            button_img_dictionary[additional_var] = open_file_as_tk_image(suzipu_to_info(additional_var).button_image_filename)
            statistics_text_var_dictionary[additional_var] = tk.StringVar()

        button_img_dictionary[Symbol.NONE] = open_file_as_tk_image(suzipu_to_info(Symbol.NONE).button_image_filename)

        return button_img_dictionary, statistics_text_var_dictionary

    def _create_frame(self):
        selection_frame = tk.Frame(self.frame)

        for idx, melody_var in enumerate(dataclasses.astuple(SuzipuMelodySymbol())):
            current_image = tk.Label(selection_frame, image=self.button_img_dictionary[melody_var], state="disabled", relief="sunken")
            current_text = tk.Label(selection_frame, textvariable=self.statistics_text_var_dictionary[melody_var], state="disabled", relief="sunken", width=3)
            self.widgets += [current_text, current_image]
            current_image.grid(row=0, column=idx, padx=5, pady=5)
            current_text.grid(row=1, column=idx, padx=5, pady=5)
        for idx, additional_var in enumerate(dataclasses.astuple(SuzipuAdditionalSymbol())):
            current_image = tk.Label(selection_frame, image=self.button_img_dictionary[additional_var], state="disabled", relief="sunken")
            current_text = tk.Label(selection_frame, textvariable=self.statistics_text_var_dictionary[additional_var], state="disabled", relief="sunken", width=3)
            self.widgets += [current_text, current_image]
            current_image.grid(row=2, column=idx, padx=5, pady=5)
            current_text.grid(row=3, column=idx, padx=5, pady=5)

        selection_frame.pack()

    def set_state(self, boolean):
        state = "disabled"
        if boolean:
            state = "normal"

        for widget in self.widgets:
            widget.config(state=state)

    def set_statistics(self, dictionary):
        for key in self.statistics_text_var_dictionary:
            self.statistics_text_var_dictionary[key].set("0")
        for key in dictionary:
            self.statistics_text_var_dictionary[key].set(dictionary[key])

    def get_frame(self):
        return self.frame


class NoteFrames:
    def __init__(self, parent_frame):
        self.frame = tk.Frame(parent_frame)
        self.widgets = []
        self.scale_degree_vars_list = []
        self.scale_degree_label_list = []
        self.suzipu_images_list = []
        self._suzipu_images = _create_suzipu_images()
        self._default_bg_color = None

    def get_frame(self):
        lvlv_list = ["黄", "大", "太", "夹", "姑", "仲", "蕤", "林", "夷", "南", "无", "应", "黄清", "大清", "太清",
                     "夹清"]
        gongche_list = ["合", "下四", "四", "下一", "一", "上", "勾", "尺", "下工", "工", "下凡", "凡", "六",
                        "下五", "五", "高五"]

        labels_frame = tk.Frame(self.frame)
        lvlv_label = tk.Label(labels_frame, text="律吕")
        gongche_label = tk.Label(labels_frame, text="工尺")
        scale_degree_label = tk.Label(labels_frame, text="声音阶")
        suzipu_label = tk.Label(labels_frame, text="俗字谱")

        lvlv_label.grid(row=0, column=0, padx=10, pady=5)
        gongche_label.grid(row=1, column=0, padx=10, pady=5)
        scale_degree_label.grid(row=2, column=0, padx=10, pady=5)
        suzipu_label.grid(row=3, column=0, padx=10, pady=5)

        labels_frame.grid(row=0, column=0)

        for idx in range(len(lvlv_list)):
            subframe = tk.LabelFrame(self.frame)
            textvar = tk.StringVar()
            self.scale_degree_vars_list.append(textvar)

            lvlv_label = tk.Label(subframe, text=lvlv_list[idx])
            gongche_label = tk.Label(subframe, text=gongche_list[idx])
            scale_degree_label = tk.Label(subframe, textvariable=textvar, relief="sunken", width=3)
            suzipu_label = tk.Label(subframe, image=self._suzipu_images[Symbol.NONE], relief="sunken")
            self.suzipu_images_list.append(suzipu_label)
            self.scale_degree_label_list.append(scale_degree_label)

            lvlv_label.grid(row=0, column=0, padx=10, pady=5)
            gongche_label.grid(row=1, column=0, padx=10, pady=5)
            scale_degree_label.grid(row=2, column=0, padx=10, pady=5)
            suzipu_label.grid(row=3, column=0, padx=10, pady=5)

            subframe.grid(row=0, column=idx+1)
            self.widgets += [lvlv_label, gongche_label, scale_degree_label, suzipu_label]

        self._default_bg_color = suzipu_label.cget("bg")
        return self.frame

    def update(self, mode: GongdiaoMode):
        final_note = mode.final_note
        tone_inventory = get_tone_inventory(mode.gong_lvlv)

        for idx in range(len(self.scale_degree_vars_list)):
            scale_degree = tone_inventory[idx] if tone_inventory[idx] else ""
            gongche_melody_symbol = dataclasses.astuple(GongcheMelodySymbol())[idx]

            pitch = gongche_melody_symbol if gongche_melody_symbol == mode.convert_pitch(gongche_melody_symbol) else None

            self.scale_degree_vars_list[idx].set(scale_degree)
            self.suzipu_images_list[idx].config(image=self._suzipu_images[pitch])

            self.scale_degree_label_list[idx].config(bg="aquamarine" if scale_degree == final_note else self._default_bg_color)

    def set_state(self, boolean):
        state = "disabled"
        if boolean:
            state = "normal"
        for widget in self.widgets:
            widget.config(state=state)


class ModeFrame:
    def __init__(self, window_handle, mode_variable, on_get_mode_string=lambda: None):
        self.window_handle = window_handle
        self.frame = tk.LabelFrame(self.window_handle, text="Mode")

        self.mode_variable = mode_variable
        self.mode_gong_lvlv = tk.IntVar()
        self.mode_final_note = tk.StringVar()
        self.mode_final_note.set("宫")

        self.widgets = None
        self.get_mode_string = on_get_mode_string

        self.note_frames = NoteFrames(self.frame)

        self._create_frame()

    def get_properties(self):
        return ModeProperties(self.mode_gong_lvlv.get(), self.mode_final_note.get())

    def set_properties(self, mode_properties: ModeProperties):
        self.mode_gong_lvlv.set(mode_properties.gong_lvlv)
        self.mode_final_note.set(mode_properties.final_note)

    def _create_frame(self):
        def on_update_mode_properties(*args, **kwargs):
            mode = GongdiaoModeList.from_string(self.mode_variable.get())
            self.mode_final_note.set(mode.final_note)
            self.mode_gong_lvlv.set(mode.gong_lvlv)

        def on_infer_mode():
            mode_string = self.get_mode_string()
            mode = GongdiaoModeList.from_string(chinese_converter.to_simplified(mode_string))
            self.mode_variable.set(mode.name)
            self.mode_gong_lvlv.set(mode.gong_lvlv)
            self.mode_final_note.set(mode.final_note)

        def on_custom_mode():
            def execute_custom_mode_window():
                custom_mode_window = tk.Toplevel()
                gong_lvlv_var = tk.StringVar()
                gong_lvlv_var.set(Lvlv.to_string(Lvlv.HUANG_ZHONG))
                final_note_var = tk.StringVar()
                final_note_var.set(GongdiaoStep.GONG)
                exit_save_var = tk.BooleanVar()
                exit_save_var.set(False)

                def on_destroy_save_changes():
                    exit_save_var.set(True)
                    custom_mode_window.destroy()

                lvlv_list = [Lvlv.to_string(lvlv) for lvlv in dataclasses.astuple(Lvlv())]
                final_note_list = dataclasses.astuple(GongdiaoStep())

                selection_frame = tk.Frame(custom_mode_window)
                lvlv_label = tk.Label(selection_frame, text="Mode's 宫")
                lvlv_selector = tk.OptionMenu(selection_frame, gong_lvlv_var, gong_lvlv_var.get(), *lvlv_list)
                final_note_label = tk.Label(selection_frame, text="Mode's Final Note")
                final_note_selector = tk.OptionMenu(selection_frame, final_note_var, final_note_var.get(), *final_note_list)

                lvlv_label.grid(row=0, column=0)
                lvlv_selector.grid(row=0, column=1)
                final_note_label.grid(row=1, column=0)
                final_note_selector.grid(row=1, column=1)

                ok_button = tk.Button(custom_mode_window, text="OK", command=on_destroy_save_changes)
                selection_frame.grid(row=0, column=0)
                ok_button.grid(row=1, column=0)

                custom_mode_window.wait_window()

                return exit_save_var.get(), gong_lvlv_var.get(), final_note_var.get()

            exit_save_var, gong_lvlv_string, final_note = execute_custom_mode_window()

            if exit_save_var:
                gong_lvlv = Lvlv.from_string(gong_lvlv_string)

                mode = GongdiaoModeList.from_properties(ModeProperties(gong_lvlv, final_note))
                self.mode_variable.set(mode.name)
                self.mode_gong_lvlv.set(mode.gong_lvlv)
                self.mode_final_note.set(mode.final_note)

        sub_frame = tk.Frame(self.frame)
        mode_names = [mode.name for mode in dataclasses.astuple(GongdiaoModeList())]
        mode_menu = tk.OptionMenu(sub_frame, self.mode_variable, "", *mode_names, command=on_update_mode_properties)
        infer_mode_button = tk.Button(sub_frame, text="Infer Mode from Segmentation Boxes", command=on_infer_mode)
        custom_mode_button = tk.Button(sub_frame, text="Custom Mode Picker", command=on_custom_mode)

        mode_menu.grid(row=0, column=0)
        infer_mode_button.grid(row=0, column=1)
        custom_mode_button.grid(row=0, column=2)

        zhuyin_label = tk.Label(self.frame, text="(Final is marked in cyan)")
        sub_frame.grid(row=0, column=0)
        self.note_frames.get_frame().grid(row=1, column=0)
        zhuyin_label.grid(row=2, column=0)

        self.widgets = [mode_menu, infer_mode_button, custom_mode_button]

    def set_state(self, boolean):
        state = "disabled"
        if boolean:
            state = "normal"
            self.note_frames.update(GongdiaoModeList.from_string(chinese_converter.to_simplified(self.mode_variable.get())))
        for widget in self.widgets:
            widget.config(state=state)
        self.note_frames.set_state(boolean)

    def get_frame(self):
        return self.frame


class AdditionalInfoFrame:
    def __init__(self, window_handle, mode_variable, on_save_notation=lambda: None, on_save_musicxml=lambda: None, get_mode_string=lambda: None):
        self.window_handle = window_handle
        self.frame = tk.Frame(self.window_handle)
        self.mode_statistics_frame = tk.Frame(self.frame)

        self.mode_frame = ModeFrame(self.mode_statistics_frame, mode_variable, get_mode_string)
        self.statistics_frame = StatisticsFrame(self.mode_statistics_frame)
        self.display_frame = DisplayNotesFrame(self.frame, on_save_notation, on_save_musicxml)

        self.mode_frame.get_frame().grid(row=0, column=0, padx=5, pady=5)
        self.statistics_frame.get_frame().grid(row=1, column=0, padx=5, pady=5)

        self.mode_statistics_frame.grid(row=0, column=0, padx=5, pady=5)
        self.display_frame.get_frame().grid(row=0, column=1, padx=5, pady=5)

    def set_state(self, boolean):
        self.statistics_frame.set_state(boolean)
        self.display_frame.set_state(boolean)
        self.mode_frame.set_state(boolean)

    def set_image(self, image):
        self.display_frame.set_image(image)

    def set_statistics(self, dictionary):
        self.statistics_frame.set_statistics(dictionary)

    def get_frame(self):
        return self.frame

    def is_jianpu(self):
        return self.display_frame.is_jianpu()

    def get_transposition(self):
        return self.display_frame.get_transposition()

    def get_mode_properties(self):
        return self.mode_frame.get_properties()

    def set_mode_properties(self, mode_properties: ModeProperties):
        return self.mode_frame.set_properties(mode_properties)