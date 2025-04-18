import copy
import dataclasses
import tkinter as tk

from src.config import FULL_NOTATION_NAME
from src.notation_editor_auxiliary import DisplayState, NotationState, NewSaveLoadFrame, EditMetadataButton, \
    InputNoteFrame, DisplayOptionsFrame, NotationOpenCvWindow
from src.widgets_auxiliary import on_closing


class NotationMainWindow:
    def __init__(self):
        self.main_window = tk.Tk()
        self.frame = tk.Frame(self.main_window)
        self.display_state = DisplayState(self.frame)
        self.notation_state = NotationState(self.frame, self.display_state)
        self.display_state.plugin_name = self.notation_state.notation_type
        self.opencv_window = NotationOpenCvWindow(f"{FULL_NOTATION_NAME} - Notation Window", self.notation_state)

    def exec(self):
        self.main_window.title(f"{FULL_NOTATION_NAME} - Main Window")
        self.display_state.update_image(self.notation_state)

        new_save_load = NewSaveLoadFrame(self.frame, self.notation_state).get_frame()
        new_save_load.pack()

        edit_metadata = EditMetadataButton(self.frame, self.notation_state).get_frame()
        edit_metadata.pack()

        display_options = DisplayOptionsFrame(self.frame, self.notation_state).get_frame()
        display_options.pack(side=tk.TOP, fill=tk.BOTH, pady=10)

        edit_metadata = InputNoteFrame(self.frame, self.notation_state).get_frame()
        edit_metadata.pack(side=tk.LEFT, fill=tk.BOTH)

        self.display_state.music_listframe.pack(side=tk.RIGHT, fill=tk.BOTH)

        def start_opencv_timer():
            def handle_opencv_window():
                self.notation_state.display_state.image_to_draw = copy.deepcopy(self.notation_state.display_state.image_to_save)
                self.opencv_window.draw_and_handle_clicks(self.notation_state.display_state.image_to_draw, self.notation_state.display_state.idx_boxes)
            handle_opencv_window()
            self.main_window.after(1, start_opencv_timer)

        start_opencv_timer()
        self.frame.pack(padx=10, pady=10)
        self.main_window.protocol("WM_DELETE_WINDOW", on_closing(self.main_window))
        self.main_window.mainloop()


if __name__ == "__main__":
    window = NotationMainWindow()
    window.exec()
