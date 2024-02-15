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


class FashionCNN(nn.Module):
    def __init__(self, num_output_classes):
        super(FashionCNN, self).__init__()

        self.layer1 = nn.Sequential(
            nn.Conv2d(in_channels=1, out_channels=32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        self.layer2 = nn.Sequential(
            nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )

        self.fc1 = nn.Linear(in_features=64 * 6 * 6, out_features=600)
        self.drop = nn.Dropout2d(0.25)
        self.fc2 = nn.Linear(in_features=600, out_features=120)
        self.fc3 = nn.Linear(in_features=120, out_features=num_output_classes)
        self.logits = nn.LogSoftmax(dim=1)

    def forward(self, x):
        out = self.layer1(x)
        out = self.layer2(out)
        out = out.view(out.size(0), -1)
        out = self.fc1(out)
        out = self.drop(out)
        out = self.fc2(out)
        out = self.fc3(out)
        out = self.logits(out)

        return out

    def get_representation(self, x):
        out = self.layer1(x)
        out = self.layer2(out)
        out = out.view(out.size(0), -1)
        out = self.fc1(out)
        out = self.drop(out)
        out = self.fc2(out)
        return out


class TemperatureScalingCalibrationModule(nn.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model

        # the single temperature scaling parameter, the initialization value doesn't
        # seem to matter that much based on some ad-hoc experimentation
        self.temperature = nn.Parameter(torch.ones(1))

    def get_representation(self, x):
        return self.model.get_representation(x)

    def forward_unscaled(self, x):
        logits = self.model(x)
        scores = nn.functional.softmax(logits, dim=1)
        return scores

    def forward(self, x):
        scaled_logits = self.forward_logit(x)
        scores = nn.functional.softmax(scaled_logits, dim=1)
        return scores

    def forward_logit(self, x):
        logits = self.model(x)
        return logits / self.temperature

    def fit(self, device, data_loader, n_epochs: int = 10, batch_size: int = 64, lr: float = 0.01):
        """fits the temperature scaling parameter."""
        assert isinstance(data_loader, DataLoader), "data_loader must be an instance of DataLoader"

        print(self.temperature.requires_grad)

        self.freeze_base_model()
        criterion = nn.NLLLoss()
        optimizer = optim.SGD(self.parameters(), lr=lr)

        for epoch in range(n_epochs):
            for batch in data_loader:
                images, labels, _ = batch
                images, labels = images.to(device), labels.to(device)

                self.zero_grad()
                scaled_logits = self.forward_logit(images)  # Use forward to get scaled logits
                loss = criterion(scaled_logits, labels)
                loss.backward()
                optimizer.step()

        return self

    def freeze_base_model(self):
        """remember to freeze base model's parameters when training temperature scaler"""
        self.model.eval()
        for parameter in self.model.parameters():
            parameter.requires_grad = False
        return self


def remove_small_blobs(image):  # remove small isolated connected black areas
    noise_removal_threshold = 1
    mask = np.ones_like(image) * 255
    contours, hierarchy = cv2.findContours(255 - image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    for contour in contours:
        area = cv2.contourArea(contour)
        if area >= noise_removal_threshold:
            cv2.fillPoly(mask, [contour], 0)
    return mask


def crop_excess_whitespace(image):
    gray = 255 * (image < 128).astype(np.uint8)  # reverse the colors
    coords = cv2.findNonZero(gray)  # Find all non-zero points (text)
    x, y, w, h = cv2.boundingRect(coords)  # Find minimum spanning bounding box
    rect = image[y:y + h, x:x + w]
    return rect


def load_transforms():
    def shrink(target_size=28):
        def inner(input_image):
            t_size = target_size - 7

            original_width = input_image.shape[-1]
            original_height = input_image.shape[-2]
            aspect_ratio = original_width / original_height

            if aspect_ratio > 1:
                w = int(t_size)
                h = int(t_size / aspect_ratio)
            else:
                w = int(t_size * aspect_ratio)
                h = int(t_size)

            output_image = transforms.Resize(size=(h, w), interpolation=transforms.InterpolationMode.NEAREST_EXACT)(
                input_image)
            return output_image

        return inner

    def paste_to_square(target_size=28):
        def inner(input_image):
            ## Modify the function to extend the
            ## input image to a square of 40x40.
            ## Tip: This can be done by clever use
            ## of the Pad function
            ## https://pytorch.org/vision/stable/generated/torchvision.transforms.Pad.html
            ## Also make sure that the added padding
            ## on each side is random, i.e., the
            ## data itself is augmented by its
            ## position in the square.

            pad_width = target_size - input_image.shape[-1]
            pad_height = target_size - input_image.shape[-2]

            left_pad = pad_width // 2
            top_pad = pad_height // 2

            right_pad = pad_width - left_pad
            bottom_pad = pad_height - top_pad

            output_image = transforms.Pad(padding=(left_pad, top_pad, right_pad, bottom_pad), fill=1)(input_image)
            return output_image

        return inner

    def normalize():
        mean = 0.8497
        std = 0.0518
        return transforms.Normalize(mean=mean, std=std)

    evaluation_transforms = transforms.Compose([
        transforms.ToTensor(),
        shrink(),
        paste_to_square(),
        lambda img: transforms.functional.invert(img),  # inverts image, needed for rotations
        normalize(),  # normalize mean and variance
    ])

    display_transforms = transforms.Compose([
        transforms.ToTensor(),
        shrink(target_size=60),
        paste_to_square(target_size=60),
        lambda img: transforms.functional.invert(img),  # inverts image, needed for rotations
        normalize(),  # normalize mean and variance
    ])

    return {
        "evaluation": evaluation_transforms,
        "display": display_transforms,
        "class_to_annotation": {
            "pitch": {0: "HE", 1: "SI", 2: "YI", 3: "SHANG", 4: "GOU", 5: "CHE", 6: "GONG", 7: "FAN", 8: "LIU", 9: "WU",
                      10: "GAO_WU"},
            "secondary": {0: None, 1: "DA_DUN", 2: "XIAO_ZHU", 3: "DING_ZHU", 4: "DA_ZHU", 5: "ZHE", 6: "YE"}
        }}


def load_model():
    pitch_model = TemperatureScalingCalibrationModule(FashionCNN(num_output_classes=11))
    pitch_model.load_state_dict(torch.load("./src/plugins/suzipu_lvlvpu_gongchepu/model_pitch.std"))
    secondary_model = TemperatureScalingCalibrationModule(FashionCNN(num_output_classes=7))
    secondary_model.load_state_dict(torch.load("./src/plugins/suzipu_lvlvpu_gongchepu/model_secondary.std"))

    pitch_model.eval()
    secondary_model.eval()

    with open("./src/plugins/suzipu_lvlvpu_gongchepu/umap_models.pkl", "rb") as file_handle:
        umap_models = pickle.load(file_handle)
    with open("./src/plugins/suzipu_lvlvpu_gongchepu/umap_embeddings.pkl", "rb") as file_handle:
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
        image = models["umap_embeddings"]["display_images"][idx]
        edition = models["umap_embeddings"]["editions"][idx]
        annotation = transformations["class_to_annotation"]["pitch"][models["umap_embeddings"]["annotations"][idx]["pitch"]]

        return {"image": cv_to_tkinter_image(image.detach().numpy()),
                "edition": edition,
                "distance": distance,
                "similarity": 1 / distance if distance > 0 else 9999,
                "annotation": annotation}

    def get_dict_secondary(distance, idx):
        image = models["umap_embeddings"]["display_images"][idx]
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
            image_list[idx] = torch.zeros([1, 28, 28])
            empty_idxs.append(idx)

    notation = predict_notation(image_list, models, transformations)
    update_window(75)
    similar = predict_similar(image_list, models, transformations)
    update_window(100)

    return {"prediction": notation,
            "similarity": similar,
            "empty_idxs": empty_idxs}