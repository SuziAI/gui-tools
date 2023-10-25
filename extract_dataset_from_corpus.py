import argparse
import json
import os

import cv2

from src.auxiliary import get_image_from_box, BoxProperty, ListCircle


def extract_dataset_from_corpus(corpus_dir, output_dir):
    def get_folder_contents(path, extension=None):
        file_list = []
        try:
            for file_path in sorted(os.listdir(path)):
                file_path = os.path.join(path, file_path)
                if os.path.isdir(file_path):
                    file_list += get_folder_contents(file_path, extension)
                if not extension or file_path.lower().endswith(f'.{extension}'):
                    file_list.append(file_path)
        except Exception as e:
            print(f"Could not read files from directory {path}. {e}")
        return file_list

    def construct_image(image_name_circle, left_counter, right_counter):
        images = []

        for idx in range(-left_counter,
                         right_counter + 1):
            image_name = image_name_circle.get_nth_from_current(idx)
            images.append(cv2.cvtColor(cv2.imread(image_name), cv2.COLOR_BGR2RGB))

        max_width, max_height = 0, 0
        for image in images:
            max_height = max(image.shape[0], max_height)
            max_width = max(image.shape[1], max_width)

        for idx in range(len(images)):
            images[idx] = cv2.copyMakeBorder(
                src=images[idx],
                top=0,
                bottom=max_height - images[idx].shape[0],
                left=0,
                right=max_width - images[idx].shape[1],
                borderType=cv2.BORDER_CONSTANT,
                value=[255, 255, 255]
            )
        images.reverse()
        current_image = cv2.hconcat(images)
        return current_image

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    text_annotations = []
    music_annotations = []

    text_dir = os.path.join(output_dir, "./Text")
    music_dir = os.path.join(output_dir, "./Music")
    if not os.path.exists(text_dir):
        os.makedirs(text_dir)
    if not os.path.exists(music_dir):
        os.makedirs(music_dir)

    json_files = get_folder_contents(corpus_dir, "json")
    for file_name in json_files:
        with open(file_name, "r") as file_handle:
            segmentation_data = json.load(file_handle)
            image_paths = [os.path.join(os.path.dirname(file_name), path) for path in segmentation_data["images"]]
            circle = ListCircle(image_paths)
            circle.set_if_present(image_paths[0])
            image = construct_image(image_name_circle=circle, left_counter=0, right_counter=len(image_paths)-1)

            box_list = segmentation_data["content"]

            for idx, box in enumerate(box_list):
                is_excluded = False
                try:
                    is_excluded = box["is_excluded_from_dataset"]
                except:
                    pass

                if not is_excluded:  # only save in dataset when not excluded
                    current_type = box["box_type"]
                    if current_type != BoxProperty.UNMARKED:
                        try:
                            cut_out_text_image = get_image_from_box(image, box["text_coordinates"])
                            text_annotation = box["text_content"]
                            box_file_name = f"{os.path.basename(image_paths[0])}_{idx}.png"
                            box_file_path = os.path.join(text_dir, box_file_name)
                            text_annotations.append({
                                "file_name": box_file_name,
                                "type": current_type,
                                "annotation": text_annotation})
                            cv2.imwrite(box_file_path, cut_out_text_image)
                        except:
                            pass

                        try:
                            cut_out_notation_image = get_image_from_box(image, box["notation_coordinates"])
                            notation_annotation = box["notation_content"]
                            box_file_name = f"{os.path.basename(image_paths[0])}_{idx}.png"
                            box_file_path = os.path.join(music_dir, box_file_name)
                            music_annotations.append({
                                "file_name": box_file_name,
                                "type": current_type,
                                "annotation": notation_annotation})
                            cv2.imwrite(box_file_path, cut_out_notation_image)
                        except:
                            pass

        with open(os.path.join(music_dir, "dataset.json"), "w") as output_file_handle:
            json.dump(music_annotations, output_file_handle)
        with open(os.path.join(text_dir, "dataset.json"), "w") as output_file_handle:
            json.dump(text_annotations, output_file_handle)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Suzipu Annotated OMR Dataset Export Script.")

    parser.add_argument("--corpus_dir", required=True, default=None,
                        help="Path to the folder which contains the corpus files (JSON format). The folder is checked "
                             "recursively for any JSON files placed inside this folder or subfolders.")
    parser.add_argument("--output_dir", required=True, default=None,
                        help="Path to the output folder to which the dataset is saved. If it doesn't exist, the script "
                             "will try to create the folder.")

    extract_dataset_from_corpus(parser.parse_args().corpus_dir, parser.parse_args().output_dir)
