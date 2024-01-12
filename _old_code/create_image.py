import os
import shutil

import cv2
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


RESULTS_DIR = 'results'

# delete the results folder if it exists
if os.path.exists(RESULTS_DIR):
    shutil.rmtree(RESULTS_DIR)

os.makedirs(RESULTS_DIR, exist_ok=True)

TEMPLATE_IMG_PATH = 'backgrounds/bgr1.png'
CSV_DATA_PATH = 'data/data.csv'

TITLE_FONT = ImageFont.truetype('fonts/OpenSans-ExtraBold.ttf', 72)
TEXT_FONT = ImageFont.truetype('fonts/OpenSans-Regular.ttf', 54)
SOURCE_FONT = ImageFont.truetype('fonts/OpenSans-ExtraBold.ttf', 54)

WHITE_COLOR = (255, 255, 255)


def resize_image(img):
    info_img_default_height = 900
    # Get the original height and width
    original_height, original_width = img.shape[:2]

    # Calculate the new width based on the desired height (300px)
    new_width = int((info_img_default_height / original_height) * original_width)

    # Resize the image while keeping the aspect ratio
    resized_img = cv2.resize(
        img, (new_width, info_img_default_height), interpolation=cv2.INTER_AREA
    )

    return resized_img


def merge_info_img(template_img, info_img):
    # resize info image
    info_img = resize_image(info_img)

    # get the width of the template and info image
    template_width = template_img.shape[1]
    info_width = info_img.shape[1]

    # merge info image to template image start from y = 400, and make the info in the center of the template
    template_img[
        400:1300,
        int((template_width - info_width) / 2) : int((template_width + info_width) / 2),
    ] = info_img

    return template_img


def draw_text_with_width_limit(draw, text, x_start, x_end, y_position, font, color):
    words = text.split()
    lines = []
    current_line = ''

    for word in words:
        test_line = current_line + word + ' '
        text_width, _ = draw.textsize(test_line, font=font)

        if text_width <= (x_end - x_start):
            current_line = test_line
        else:
            lines.append(current_line.strip())
            current_line = word + ' '

    if current_line:
        lines.append(current_line.strip())

    y = y_position
    for line in lines:
        text_width, _ = draw.textsize(line, font=font)
        x = x_start  # Align text to the left within the boundaries
        draw.text((x, y), line, color, font=font)
        y += font.getsize(line)[1]  # Move to the next line

    return y


def merge_text(title, descripton, img):
    # convert the image to PIL format and keep the RGB format
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)

    # create a draw object
    draw = ImageDraw.Draw(img)

    # draw the title
    y_start = 1350
    decs_y = draw_text_with_width_limit(
        draw, title, 190, 3410, y_start, TITLE_FONT, WHITE_COLOR
    )

    # draw the description
    source_y = draw_text_with_width_limit(
        draw, descripton, 190, 3410, decs_y + 20, TEXT_FONT, WHITE_COLOR
    )

    # draw the source
    draw.text(
        (190, source_y + 20),
        'Nguồn VnExpress',
        WHITE_COLOR,
        font=SOURCE_FONT,
    )

    # convert the image back to cv2 format
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    return img


if __name__ == '__main__':
    # # read csv file
    df = pd.read_csv(CSV_DATA_PATH)
    for index, row in df.iterrows():
        # get the title and description
        title = row['title']
        description = row['description']

        # get the info image path
        img_path = row['image_path']
        info_img = cv2.imread(img_path)

        # read template image
        template_img = cv2.imread(TEMPLATE_IMG_PATH)

        # merge the image
        merged_img = merge_info_img(template_img, info_img)

        # merge the text
        merged_img = merge_text(title, description, merged_img)

        # save the result
        cv2.imwrite(f'{RESULTS_DIR}/{index}.png', merged_img)
