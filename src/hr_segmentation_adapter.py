import cv2
import torch
import argparse
import torch
from torch.autograd import Variable
import torchvision
from torchvision.ops import nms
import os
from PIL import Image
import numpy as np
from skimage.draw import rectangle_perimeter

import sys

sys.path.append("./src/HRCenterNet")
from models.HRCenterNet import HRCenterNet as segmentation_net

#sys.path.append("./HRRegionNet")
#from models.HRRegionNet import HRRegionNet as segmenation_net

#try:
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
#except Exception as e:
#    device = torch.device("cpu")

input_size = 512
output_size = 128


def load_model(weights_path):
    try:
        if weights_path is not None:
            #print("Load checkpoint from " + segmentation_weights_path)
            checkpoint = torch.load(weights_path, map_location="cpu")

        model = segmentation_net()
        model.load_state_dict(checkpoint['model'])
        model = model.to(device)
        return model
    except Exception as e:
        print(f"Could not create model. {e}")


def get_rectangles(img_shape, prediction, nms_score=0.3, iou_threshold=0.1):
    bbox = list()
    score_list = list()

    heatmap = prediction.data.cpu().numpy()[0, 0, ...]
    offset_y = prediction.data.cpu().numpy()[0, 1, ...]
    offset_x = prediction.data.cpu().numpy()[0, 2, ...]
    width_map = prediction.data.cpu().numpy()[0, 3, ...]
    height_map = prediction.data.cpu().numpy()[0, 4, ...]

    for j in np.where(heatmap.reshape(-1, 1) >= nms_score)[0]:
        row = j // output_size
        col = j - row * output_size

        bias_x = offset_x[row, col] * (img_shape[0] / output_size)
        bias_y = offset_y[row, col] * (img_shape[1] / output_size)

        width = width_map[row, col] * output_size * (img_shape[0] / output_size)
        height = height_map[row, col] * output_size * (img_shape[1] / output_size)

        score_list.append(heatmap[row, col])

        row = row * (img_shape[0] / output_size) + bias_y
        col = col * (img_shape[1] / output_size) + bias_x

        top = row - width // 2
        left = col - height // 2
        bottom = row + width // 2
        right = col + height // 2

        bbox.append([top, left, bottom, right])

    _nms_index = torchvision.ops.nms(torch.FloatTensor(bbox), scores=torch.flatten(torch.FloatTensor(score_list)),
                                     iou_threshold=iou_threshold)

    output_values = []
    for k in range(len(_nms_index)):
        top, left, bottom, right = bbox[_nms_index[k]]

        start = (int(left), int(top))
        end = (int(right), int(bottom))

        output_values.append((start, end))
    return output_values


def get_raw_prediction(input_img, model):
    test_tx = torchvision.transforms.Compose([
        torchvision.transforms.ToTensor(),
        torchvision.transforms.Resize((input_size, input_size), antialias=True),
        #torchvision.transforms.ToTensor(),
    ])

    input_img = cv2.cvtColor(input_img, cv2.COLOR_BGR2RGB)
    input_img = Image.fromarray(input_img).convert("RGB")

    image_tensor = test_tx(input_img)
    image_tensor = image_tensor.unsqueeze_(0)
    inp = Variable(image_tensor)
    inp = inp.to(device, dtype=torch.float)
    prediction = model(inp)
    return prediction


def predict_boxes(input_img, weights_path):
    model = load_model(weights_path=weights_path)
    model.eval()

    raw_prediction = get_raw_prediction(input_img, model)
    rectangle_list = get_rectangles(input_img.shape, raw_prediction)

    return rectangle_list