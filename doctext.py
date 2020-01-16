import argparse
from enum import Enum
import io
import os

from google.cloud import vision
from google.cloud.vision import types
from PIL import Image, ImageDraw
import cv2


class FeatureType(Enum):
    PAGE = 1
    BLOCK = 2
    PARA = 3
    WORD = 4
    SYMBOL = 5


def draw_boxes(image, bounds, color):
    """Draw a border around the image using the hints in the vector list."""
    draw = ImageDraw.Draw(image)

    for bound in bounds:
        draw.polygon(
            [
                bound.vertices[0].x,
                bound.vertices[0].y,
                bound.vertices[1].x,
                bound.vertices[1].y,
                bound.vertices[2].x,
                bound.vertices[2].y,
                bound.vertices[3].x,
                bound.vertices[3].y,
            ],
            None,
            color,
        )
    return image


def get_document_bounds(image_file, feature):
    """Returns document bounds given an image."""
    client = vision.ImageAnnotatorClient()

    bounds = []
    text = []

    with io.open(image_file, "rb") as image_file:
        content = image_file.read()

    image = types.Image(content=content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    # Collect specified feature bounds by enumerating all document features
    for page in document.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    for symbol in word.symbols:
                        if feature == FeatureType.SYMBOL:
                            bounds.append(symbol.bounding_box)
                            text.append(symbol.text)

                    if feature == FeatureType.WORD:
                        bounds.append(word.bounding_box)
                        text.append(word.text)

                if feature == FeatureType.PARA:
                    bounds.append(paragraph.bounding_box)
                    text.append(paragraph.text)

            if feature == FeatureType.BLOCK:
                bounds.append(block.bounding_box)
                text.append(block.text)

    # The list `bounds` contains the coordinates of the bounding boxes.
    return bounds, text


def render_doc_text(file_in, path_out, feature):
    bounds, text = get_document_bounds(file_in, feature)

    image = Image.open(file_in)
    draw_boxes(image, bounds, "red")
    image.save(os.path.join(path_out, "rendered.jpg"))

    img = cv2.imread(file_in)
    for bound, t in zip(bounds, text):
        print(bound)
        print(t)
        print("!!!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("detect_file", help="The image for text detection.")
    parser.add_argument("out_path", help="Output path")
    args = parser.parse_args()

    render_doc_text(args.detect_file, args.out_path, FeatureType.SYMBOL)
