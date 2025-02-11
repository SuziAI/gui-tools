import cv2
import numpy as np
from skimage.util import random_noise
import torch
from torch import optim
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
import torchvision.transforms as transforms
import random


def shrink(is_random=True, target_size=20):
    def inner(input_image):

        t_size = random.randint(int(0.75 * target_size), int(target_size + 2)) if is_random else target_size

        original_width = input_image.shape[-1]
        original_height = input_image.shape[-2]
        aspect_ratio = original_width / original_height * random.uniform(0.6,
                                                                         1.5) if is_random else original_width / original_height

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


def paste_to_square(is_random=True, target_size=28):
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

        left_pad = random.randint(0, pad_width) if is_random else pad_width // 2
        top_pad = random.randint(0, pad_height) if is_random else pad_height // 2

        right_pad = pad_width - left_pad
        bottom_pad = pad_height - top_pad

        output_image = transforms.Pad(padding=(left_pad, top_pad, right_pad, bottom_pad), fill=1)(input_image)
        return output_image

    return inner


def salt_and_pepper(percentage=0.1, amount=0.001):
    def inner(input_image):
        output_image = input_image.numpy().squeeze()
        if random.uniform(0, 1) < percentage / 2:
            output_image = random_noise(output_image, mode='salt', amount=2 * amount)
        if random.uniform(0, 1) < percentage / 2:
            output_image = random_noise(output_image, mode='pepper', amount=amount)
        return torch.Tensor(output_image).unsqueeze(0)

    return inner


def erode(percentage=0.1):
    def inner(input_image):
        if random.uniform(0, 1) < percentage:  # only apply transformation according to percentage
            kernel = np.ones((2, 2), np.uint8)
            output_image = cv2.erode(input_image, kernel, iterations=1)
            return output_image
        else:
            return input_image

    return inner


def dilate(percentage=0.1):
    def inner(input_image):
        if random.uniform(0, 1) < percentage:  # only apply transformation according to percentage
            kernel = np.ones((2, 2), np.uint8)
            output_image = cv2.dilate(input_image, kernel, iterations=1)
            return output_image
        else:
            return input_image

    return inner


def remove_small_blobs(image):  # remove small isolated connected black areas
    noise_removal_threshold = 1
    mask = np.ones_like(image)*255
    contours, hierarchy = cv2.findContours(255-image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    for contour in contours:
      area = cv2.contourArea(contour)
      if area >= noise_removal_threshold:
        cv2.fillPoly(mask, [contour], 0)
    return mask


def crop_excess_whitespace(image):
    gray = 255*(image < 128).astype(np.uint8) #reverse the colors
    coords = cv2.findNonZero(gray) # Find all non-zero points (text)
    x, y, w, h = cv2.boundingRect(coords) # Find minimum spanning bounding box
    rect = image[y:y+h, x:x+w]
    return rect


class CnnModel(nn.Module):
    def __init__(self, num_classes=11, image_size=0):
        super(CnnModel, self).__init__()

        self.conv1 = nn.Conv2d(in_channels=1, out_channels=32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

        self.conv2 = nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)

        self.conv3 = nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)

        self.fc1 = nn.Linear(128 * 6 * 6, 128)  # After three 2x2 max-pool layers, 48 -> 24 -> 12 -> 6
        self.dropout = nn.Dropout(0.5)
        self.fc2 = nn.Linear(128, num_classes)

        self.logits = nn.LogSoftmax(dim=1)

    def forward(self, x):
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.pool(x)
        x = F.relu(self.bn2(self.conv2(x)))
        x = self.pool(x)
        x = F.relu(self.bn3(self.conv3(x)))
        x = self.pool(x)

        x = torch.flatten(x, start_dim=1)  # Flatten the feature maps
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        # x = self.logits(x)
        return x  # No softmax, as it's handled in CrossEntropyLoss

    def get_representation(self, x):
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.pool(x)
        x = F.relu(self.bn2(self.conv2(x)))
        x = self.pool(x)
        x = F.relu(self.bn3(self.conv3(x)))
        x = self.pool(x)

        x = torch.flatten(x, start_dim=1)  # Flatten the feature maps
        x = self.fc1(x)
        return x


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
