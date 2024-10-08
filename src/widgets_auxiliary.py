import dataclasses
import importlib
import tkinter as tk
from tkinter import messagebox

from src.auxiliary import get_class_variables, bgr_to_tkinter, box_property_to_color, BoxType, SetInt, \
    BoxManipulationAction
from src.plugins import NotationTypePlugins
from src.programstate import ProgramState


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
        self.frame = tk.LabelFrame(self.window_handle, text="Base image")

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
    def __init__(self, window_handle, program_state, selectionmode_var: tk.StringVar, boxtype_var: tk.StringVar,
                 on_click_annotate=lambda: None, on_change_mode_selection=lambda: None,
                 on_change_box_type_selection=lambda: None):
        self.window_handle = window_handle
        self.program_state = program_state
        self.frame = tk.LabelFrame(self.window_handle, text="Box Manipulation")
        self.selectionmode_var = selectionmode_var
        self.boxtype_var = boxtype_var
        self.on_click_annotate = on_click_annotate
        self.on_change_mode_selection = on_change_mode_selection
        self.on_change_box_type_selection = on_change_box_type_selection
        self.is_active = False

        self._create_frame()

    def _create_frame(self):
        left_frame = tk.Frame(self.frame)
        frame1 = tk.Frame(left_frame)
        frame2 = tk.Frame(left_frame)

        boxtype_buttons = []
        for idx, boxtype_var in enumerate(dataclasses.astuple(BoxType())):
            boxtype_buttons.append(tk.Radiobutton(frame2, text=f"{idx+1} {boxtype_var}", variable=self.boxtype_var,
                                                  value=boxtype_var, indicator=0, state="disabled",
                                                  bg=bgr_to_tkinter(box_property_to_color(boxtype_var)),
                                                  command=self.on_change_box_type_selection, underline=0))

        def _on_change_selection_mode():
            self.is_active = self.selectionmode_var.get() in [BoxManipulationAction.CREATE, BoxManipulationAction.MARK,
                                                              BoxManipulationAction.ANNOTATE]
            state = "normal" if self.is_active else "disabled"

            for boxtype_button_element in boxtype_buttons:
                boxtype_button_element.config(state=state)
            self.on_change_mode_selection()

        action_buttons = []
        for idx, selection_mode in enumerate(get_class_variables(BoxManipulationAction)):
            if selection_mode == BoxManipulationAction.ANNOTATE:
                command = lambda: [self.on_click_annotate(), _on_change_selection_mode()]
            else:
                command = _on_change_selection_mode
            button = tk.Radiobutton(frame1, text=selection_mode, variable=self.selectionmode_var, value=selection_mode, indicator=0, command=command, underline=0)
            button.grid(row=0, column=idx)
            action_buttons.append(button)

        self.program_state.gui_state.main_window.bind("<Control-n>", lambda x: action_buttons[0].invoke())
        self.program_state.gui_state.main_window.bind("<Control-c>", lambda x: action_buttons[1].invoke())
        self.program_state.gui_state.main_window.bind("<Control-m>", lambda x: action_buttons[2].invoke())
        self.program_state.gui_state.main_window.bind("<Control-d>", lambda x: action_buttons[3].invoke())
        self.program_state.gui_state.main_window.bind("<Control-r>", lambda x: action_buttons[4].invoke())
        self.program_state.gui_state.main_window.bind("<Control-o>", lambda x: action_buttons[5].invoke())
        self.program_state.gui_state.main_window.bind("<Control-a>", lambda x: action_buttons[6].invoke())

        #for idx in range(8):
        #    self.piece_properties.gui_state.main_window.bind(f"<Control-KeyPress-{idx+1}>", lambda x: boxtype_buttons[idx].invoke())
        self.program_state.gui_state.main_window.bind(f"<Control-KeyPress-1>", lambda x: boxtype_buttons[0].invoke())
        self.program_state.gui_state.main_window.bind(f"<Control-KeyPress-2>", lambda x: boxtype_buttons[1].invoke())
        self.program_state.gui_state.main_window.bind(f"<Control-KeyPress-3>", lambda x: boxtype_buttons[2].invoke())
        self.program_state.gui_state.main_window.bind(f"<Control-KeyPress-4>", lambda x: boxtype_buttons[3].invoke())
        self.program_state.gui_state.main_window.bind(f"<Control-KeyPress-5>", lambda x: boxtype_buttons[4].invoke())
        self.program_state.gui_state.main_window.bind(f"<Control-KeyPress-6>", lambda x: boxtype_buttons[5].invoke())
        self.program_state.gui_state.main_window.bind(f"<Control-KeyPress-7>", lambda x: boxtype_buttons[6].invoke())
        self.program_state.gui_state.main_window.bind(f"<Control-KeyPress-8>", lambda x: boxtype_buttons[7].invoke())

        for idx, boxtype_button in enumerate(boxtype_buttons):
            boxtype_button.grid(row=0, column=idx)

        frame1.grid(row=0, column=0, pady=4, padx=10)
        frame2.grid(row=1, column=0, pady=4, padx=10)
        left_frame.grid(row=0, column=0)

        right_frame = tk.LabelFrame(self.frame, text="Box Width")
        increment_decrement_frame = IncrementDecrementFrame(right_frame, self.program_state.gui_state.draw_box_width)
        increment_decrement_frame.get_frame().pack()
        right_frame.grid(row=0, column=1)

    def get_frame(self):
        return self.frame


class PiecePropertiesFrame:
    def __init__(self, window_handle, program_state: ProgramState):
        self.window_handle = window_handle
        self.frame = tk.LabelFrame(self.window_handle, text="Piece Properties")
        self.program_state = program_state
        self.plugins = NotationTypePlugins()

        self._create_frame()

    def _create_frame(self):
        def reset_musical_annotation(*args):
            plugin_name = self.program_state.gui_state.tk_notation_plugin_selection.get().lower()
            module = importlib.import_module(f"src.plugins.{plugin_name}")
            self.program_state.fill_all_boxes_of_type(BoxType.MUSIC, module.EMPTY_ANNOTATION, constant_fill=True)


        tk.Label(self.frame, text="Composer").grid(row=0, column=0)
        tk.Entry(self.frame, textvariable=self.program_state.gui_state.tk_current_composer).grid(row=0, column=1)
        tk.Label(self.frame, text="Notation").grid(row=1, column=0)
        self.program_state.gui_state.tk_notation_plugin_selection.set("Suzipu")
        tk.OptionMenu(self.frame, self.program_state.gui_state.tk_notation_plugin_selection, *self.plugins.plugin_names, command=reset_musical_annotation).grid(row=1, column=1)
    def get_frame(self):
        return self.frame


class SaveLoadFrame:
    def __init__(self, window_handle, on_save_image=lambda: None, on_new=lambda: None, on_save=lambda: None, on_save_text=lambda: None, on_load=lambda: None):
        self.window_handle = window_handle
        self.frame = tk.Frame(self.window_handle)
        self.on_save_image = on_save_image
        self.on_new = on_new
        self.on_save = on_save
        self.on_load = on_load
        self.on_save_text = on_save_text

        self._create_frame()

    def _create_frame(self):
        tk.Button(self.frame, text="New", command=self.on_new).grid(row=0, column=0)
        tk.Button(self.frame, text="Open", command=self.on_load).grid(row=0, column=1)
        tk.Label(self.frame, text="").grid(row=0, column=2, padx=10)
        tk.Button(self.frame, text="Save", command=self.on_save, underline=0).grid(row=0, column=3)
        tk.Label(self.frame, text="").grid(row=0, column=4, padx=10)
        tk.Button(self.frame, text="Export whole Image", command=self.on_save_image).grid(row=0, column=5)
        tk.Button(self.frame, text="Export as Text", command=self.on_save_text).grid(row=0, column=6)

    def get_frame(self):
        return self.frame


