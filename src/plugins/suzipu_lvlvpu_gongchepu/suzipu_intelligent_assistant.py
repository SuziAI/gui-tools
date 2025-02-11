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
from torch import optim
from torch.utils.data import DataLoader

from src.auxiliary import cv_to_tkinter_image
from src.plugins.suzipu_lvlvpu_gongchepu.models import *


def load_transforms():
    def normalize():
        mean = 0.7102
        std = 0.0914
        return transforms.Normalize(mean=mean, std=std)

    image_size = 48
    target_shrink = image_size - 8
    target_paste = image_size

    evaluation_transforms = transforms.Compose([
        transforms.ToTensor(),
        shrink(is_random=False, target_size=target_shrink),
        paste_to_square(is_random=False, target_size=target_paste),
        lambda img: transforms.functional.invert(img), # inverts image, needed for rotations
        normalize(), # normalize mean and variance
    ])

    return {
        "evaluation": evaluation_transforms,
        "class_to_annotation": {
            "pitch": {0: "HE", 1: "SI", 2: "YI", 3: "SHANG", 4: "GOU", 5: "CHE", 6: "GONG", 7: "FAN", 8: "LIU", 9: "WU",
                      10: "GAO_WU"},
            "secondary": {0: None, 1: "DA_DUN", 2: "XIAO_ZHU", 3: "DING_ZHU", 4: "DA_ZHU", 5: "ZHE", 6: "YE"}
        }}


def load_model():
    pitch_model = TemperatureScalingCalibrationModule(CnnModel(num_classes=11))
    pitch_model.load_state_dict(torch.load("./src/plugins/suzipu_lvlvpu_gongchepu/suzi_model_pitch.std"))
    secondary_model = TemperatureScalingCalibrationModule(CnnModel(num_classes=7))
    secondary_model.load_state_dict(torch.load("./src/plugins/suzipu_lvlvpu_gongchepu/suzi_model_secondary.std"))

    pitch_model.eval()
    secondary_model.eval()

    with open("./src/plugins/suzipu_lvlvpu_gongchepu/suzi_umap_models.pkl", "rb") as file_handle:
        umap_models = pickle.load(file_handle)
    with open("./src/plugins/suzipu_lvlvpu_gongchepu/suzi_umap_embeddings.pkl", "rb") as file_handle:
        umap_embeddings = pickle.load(file_handle)

    return {
        "model": {"pitch": pitch_model, "secondary": secondary_model},
        "umap_models": umap_models,
        "umap_embeddings": umap_embeddings,
    }


def predict_similar(image_list, models, transformations):
    concatenation = torch.cat([image.unsqueeze(0) for image in image_list])

    pitch_latent = models["model"]["pitch"].get_representation(concatenation).detach().numpy()
    secondary_latent = models["model"]["secondary"].get_representation(concatenation).detach().numpy()

    current_pitch_embedding = models["umap_models"]["pitch"](pitch_latent)
    current_secondary_embedding = models["umap_models"]["secondary"](secondary_latent)

    pitch_nbrs = NearestNeighbors(n_neighbors=3, algorithm='ball_tree').fit(
        models["umap_embeddings"]["pitch_embeddings"])
    pitch_distances, pitch_indices = pitch_nbrs.kneighbors(current_pitch_embedding)

    secondary_nbrs = NearestNeighbors(n_neighbors=3, algorithm='ball_tree').fit(
        models["umap_embeddings"]["secondary_embeddings"])
    secondary_distances, secondary_indices = secondary_nbrs.kneighbors(current_secondary_embedding)

    def get_dict_pitch(distance, idx):
        image = models["umap_embeddings"]["gui_images"][idx]
        edition = models["umap_embeddings"]["editions"][idx]
        annotation = transformations["class_to_annotation"]["pitch"][models["umap_embeddings"]["annotations"][idx]["pitch"]]

        return {"image": cv_to_tkinter_image(image.detach().numpy()),
                "edition": edition,
                "distance": distance,
                "similarity": 1 / distance if distance > 0 else 9999,
                "annotation": annotation}

    def get_dict_secondary(distance, idx):
        image = models["umap_embeddings"]["gui_images"][idx]
        edition = models["umap_embeddings"]["editions"][idx]

        annotation = transformations["class_to_annotation"]["secondary"][models["umap_embeddings"]["annotations"][idx]["secondary"]]

        return {"image": cv_to_tkinter_image(image.detach().numpy()),
                "edition": edition,
                "distance": distance,
                "similarity": 1 / distance if distance > 0 else 9999,
                "annotation": annotation}

    output = {"pitch":
                  [[get_dict_pitch(distance, idx) for distance, idx in zip(pitch_distances[IDX], pitch_indices[IDX])]
                   for IDX in range(len(image_list))],
              "secondary":
                  [[get_dict_secondary(distance, idx) for distance, idx in
                    zip(secondary_distances[IDX], secondary_indices[IDX])] for IDX in range(len(image_list))],
              }

    return output


def predict_notation(image_list, models, transformations):
    concatenation = torch.cat([image.unsqueeze(0) for image in image_list])

    pitch_predictions = models["model"]["pitch"].forward(concatenation).detach().numpy()
    secondary_predictions = models["model"]["secondary"].forward(concatenation).detach().numpy()

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
        annotations = [transformations["class_to_annotation"]["pitch"][annotation] for annotation in annotations]
        return {
            "annotations": annotations,
            "confidences": confidences
        }

    def get_dict_secondary(idx):
        annotations, confidences = get_first_three(secondary_predictions[idx])
        annotations = [transformations["class_to_annotation"]["secondary"][annotation] for annotation in annotations]
        return {
            "annotations": annotations,
            "confidences": confidences
        }

    output = {"pitch": [get_dict_pitch(idx) for idx in range(len(image_list))],
              "secondary": [get_dict_secondary(idx) for idx in range(len(image_list))],
    }

    return output


def predict_all(image_list, models, transformations, update_window=lambda x: None):
    empty_idxs = []
    for idx in range(len(image_list)):
        cropped = crop_excess_whitespace(remove_small_blobs(image_list[idx]))
        if np.prod(cropped.shape):
            image_list[idx] = transformations["evaluation"](cropped)
        else:
            image_list[idx] = torch.zeros([1, 48, 48])
            empty_idxs.append(idx)

    notation = predict_notation(image_list, models, transformations)
    update_window(75)
    similar = predict_similar(image_list, models, transformations)
    update_window(100)

    return {"prediction": notation,
            "similarity": similar,
            "empty_idxs": empty_idxs}