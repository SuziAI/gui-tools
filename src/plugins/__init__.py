import dataclasses
import os
from typing import Protocol


@dataclasses.dataclass
class NotationType:
    def __init__(self):
        self.plugin_names = []
        self.plugin_paths = {}

        try:
            for file_path in sorted(os.listdir("./src/plugins")):

                plugin_name = os.path.splitext(file_path)[0]
                extension = os.path.splitext(file_path)[-1]
                if extension == ".py" and plugin_name[0] != "_":
                    self.plugin_names.append(plugin_name.capitalize())
                    self.plugin_paths[plugin_name.capitalize()] = file_path
        except Exception as e:
            print(f"Could not read files from directory './src/plugins'. {e}")

        print("PLUGINS:", self.plugin_paths)


#class NotationAnnotationFrameProtocol(Protocol):


