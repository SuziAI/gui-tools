import copy
import pickle

import cv2
import torch
import torch.nn as nn
import torchvision.transforms as transforms
import numpy as np
import random

from PIL import ImageTk
from sklearn.neighbors import NearestNeighbors

from src.auxiliary import cv_to_tkinter_image
from src.plugins.suzipu_lvlvpu_gongchepu.models import *
from src.plugins.lvlvpu_type import ExtendedLvlv


def crop_excess_whitespace(image):
    gray = 255 * (image < 128).astype(np.uint8)  # reverse the colors
    coords = cv2.findNonZero(gray)  # Find all non-zero points (text)
    x, y, w, h = cv2.boundingRect(coords)  # Find minimum spanning bounding box
    rect = image[y:y + h, x:x + w]
    return rect


def load_transforms():
    def normalize():
        mean = 0.7148
        std = 0.0575
        return transforms.Normalize(mean=mean, std=std)

    image_size = 48
    target_shrink = image_size - 8
    target_paste = image_size

    evaluation_transforms = transforms.Compose([
        transforms.ToTensor(),
        shrink(is_random=False, target_size=target_shrink),
        paste_to_square(is_random=False, target_size=target_paste),
        lambda img: transforms.functional.invert(img),  # inverts image, needed for rotations
        normalize(),  # normalize mean and variance
    ])

    return {
        "evaluation": evaluation_transforms,
        "class_to_annotation": {
            "pitch": {0: "HE", 1: "SI", 2: "YI", 3: "SHANG", 4: "GOU", 5: "CHE", 6: "GONG", 7: "FAN", 8: "LIU", 9: "WU",
                      10: "GAO_WU"},
            "secondary": {0: None, 1: "DA_DUN", 2: "XIAO_ZHU", 3: "DING_ZHU", 4: "DA_ZHU", 5: "ZHE", 6: "YE"}
        }}


def load_model():
    pitch_model = TemperatureScalingCalibrationModule(CnnModel(num_classes=17))
    pitch_model.load_state_dict(torch.load("./src/plugins/suzipu_lvlvpu_gongchepu/lvlv_model.std"))
    pitch_model.eval()

    with open("./src/plugins/suzipu_lvlvpu_gongchepu/lvlv_umap_models.pkl", "rb") as file_handle:
        umap_models = pickle.load(file_handle)
    with open("./src/plugins/suzipu_lvlvpu_gongchepu/lvlv_umap_embeddings.pkl", "rb") as file_handle:
        umap_embeddings = pickle.load(file_handle)

    return {
        "model": {"pitch": pitch_model},
        "umap_models": umap_models,
        "umap_embeddings": umap_embeddings,
    }


def predict_similar(image_list, models):
    concatenation = torch.cat([image.unsqueeze(0) for image in image_list])

    pitch_latent = models["model"]["pitch"].get_representation(concatenation).detach().numpy()
    current_pitch_embedding = models["umap_models"](pitch_latent)
    print(current_pitch_embedding)

    pitch_nbrs = NearestNeighbors(n_neighbors=3, algorithm='ball_tree').fit(models["umap_embeddings"]["embeddings"])
    pitch_distances, pitch_indices = pitch_nbrs.kneighbors(current_pitch_embedding)

    def get_dict_pitch(distance, idx):
        image = models["umap_embeddings"]["gui_images"][idx]
        edition = models["umap_embeddings"]["editions"][idx]
        annotation = ExtendedLvlv.from_class(models["umap_embeddings"]["annotations"][idx])

        return {"image": cv_to_tkinter_image(image.detach().numpy()),
                "edition": edition,
                "distance": distance,
                "similarity": 1 / distance if distance > 0 else 9999,
                "annotation": annotation}

    output = {"pitch":
                  [[get_dict_pitch(distance, idx) for distance, idx in zip(pitch_distances[IDX], pitch_indices[IDX])]
                   for IDX in range(len(image_list))],
              }

    return output


def predict_notation(image_list, models):
    concatenation = torch.cat([image.unsqueeze(0) for image in image_list])

    pitch_predictions = models["model"]["pitch"].forward(concatenation).detach().numpy()

    def get_first_three(tensor):
        first_confidence = tensor.max()
        first_label = tensor.argmax()
        tensor[first_label] = 0

        second_confidence = tensor.max()
        second_label = tensor.argmax()
        tensor[second_label] = 0

        third_confidence = tensor.max()
        third_label = tensor.argmax()
        tensor[third_label] = 0

        return [first_label, second_label, third_label], [first_confidence, second_confidence, third_confidence]

    def get_dict_pitch(idx):
        annotations, confidences = get_first_three(pitch_predictions[idx])
        annotations = [ExtendedLvlv.from_class(annotation) for annotation in annotations]
        return {
            "annotations": annotations,
            "confidences": confidences
        }


    output = {"pitch": [get_dict_pitch(idx) for idx in range(len(image_list))]}

    return output


def predict_all(image_list, models, transformations, update_window=lambda x: None):
    empty_idxs = []
    for idx in range(len(image_list)):
        cropped = crop_excess_whitespace(image_list[idx])
        if np.prod(cropped.shape):
            image_list[idx] = transformations["evaluation"](cropped)
        else:
            image_list[idx] = torch.zeros([1, 48, 48])
            empty_idxs.append(idx)

    notation = predict_notation(image_list, models)
    update_window(75)
    similar = predict_similar(image_list, models)
    update_window(100)

    return {"prediction": notation,
            "similarity": similar,
            "empty_idxs": empty_idxs}