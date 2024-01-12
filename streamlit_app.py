import base64
import json
import os
import pickle
import re
import shutil
import uuid
import warnings

import cv2
import numpy as np
import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont


warnings.filterwarnings("ignore")


def crawl_news():
    
    
    if os.path.exists(SAVE_POST_IMG_DIR):
        shutil.rmtree(SAVE_POST_IMG_DIR)
    os.makedirs(SAVE_POST_IMG_DIR, exist_ok=True)

    response = requests.get(VNEXPRESS)

    soup = BeautifulSoup(response.text, 'html.parser')

    articles = soup.find_all('article', class_='item-news item-news-common thumb-left')
    list_url = []
    for article in articles:
        article_url = article.h2.a['href']
        list_url.append(article_url)
    list_url = list(set(list_url))


    # ---- ở trên oke
    df = pd.DataFrame(
        columns=['id', 'title', 'url', 'time', 'description', 'content', 'image_path']
    )
    list_url = list_url[:15]
    for url in list_url:
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            article_id = str(uuid.uuid4())
            title = soup.h1.text.strip()
            time = soup.find('span', class_='date').text.strip()

            time = time.split(',')[1].strip()
            year = time.split('/')[2]
            month = time.split('/')[1]
            day = time.split('/')[0]
            year = int(year)
            month = int(month)
            day = int(day)

            description_tag = soup.find('p', class_='description')

            if description_tag.span:
                description_tag.span.decompose()

            description = description_tag.text.strip()
            content = soup.find('article', class_='fck_detail').text.strip()
            picture = soup.find('div', class_='fig-picture')
            try:
                image_url = picture.img['src']
                response = requests.get(image_url)
                image_path = SAVE_POST_IMG_DIR + '/' + article_id + '.jpg'
                with open(image_path, 'wb') as f:
                    f.write(response.content)

            except:
                image_path = None

            row = {
                'id': article_id,
                'title': title,
                'url': url,
                'time': time,
                'year': year,
                'month': month,
                'day': day,
                'description': description,
                'content': content,
                'image_path': image_path,
            }
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            print('Done: ', url)
        except:
            print('Error: ', url)

    # drop row with empty image_path
    df = df.dropna(subset=['image_path'])

    # sort and get the ten latest news
    df = df.sort_values(by=['year', 'month', 'day'], ascending=False)
    df = df[:min(10, len(df))]
    return df


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


def download_button(
    object_to_download, download_filename, button_text, pickle_it=False
):
    """
    Generates a link to download the given object_to_download.
    Params:
    ------
    object_to_download:  The object to be downloaded.
    download_filename (str): filename and extension of file. e.g. mydata.csv,
    some_txt_output.txt download_link_text (str): Text to display for download
    link.
    button_text (str): Text to display on download button (e.g. 'click here to download file')
    pickle_it (bool): If True, pickle file.
    Returns:
    -------
    (str): the anchor tag to download object_to_download
    Examples:
    --------
    download_link(your_df, 'YOUR_DF.csv', 'Click to download data!')
    download_link(your_str, 'YOUR_STRING.txt', 'Click to download text!')
    """
    if pickle_it:
        try:
            object_to_download = pickle.dumps(object_to_download)
        except pickle.PicklingError as e:
            st.write(e)
            return None

    else:
        if isinstance(object_to_download, bytes):
            pass

        elif isinstance(object_to_download, pd.DataFrame):
            object_to_download = object_to_download.to_csv(index=False)

        # Try JSON encode for everything else
        else:
            object_to_download = json.dumps(object_to_download)

    try:
        # some strings <-> bytes conversions necessary here
        b64 = base64.b64encode(object_to_download.encode()).decode()

    except AttributeError as e:
        b64 = base64.b64encode(object_to_download).decode()

    button_uuid = str(uuid.uuid4()).replace('-', '')
    button_id = re.sub('\d+', '', button_uuid)

    custom_css = f""" 
        <style>
            #{button_id} {{
                background-color: rgb(255, 255, 255);
                color: rgb(38, 39, 48);
                padding: 0.25em 0.38em;
                position: relative;
                text-decoration: none;
                border-radius: 4px;
                border-width: 1px;
                border-style: solid;
                border-color: rgb(230, 234, 241);
                border-image: initial;
            }} 
            #{button_id}:hover {{
                border-color: rgb(246, 51, 102);
                color: rgb(246, 51, 102);
            }}
            #{button_id}:active {{
                box-shadow: none;
                background-color: rgb(246, 51, 102);
                color: white;
                }}
        </style> """

    dl_link = (
        custom_css
        + f'<a download="{download_filename}" id="{button_id}" href="data:file/txt;base64,{b64}">{button_text}</a><br></br>'
    )

    return dl_link


def main():
    placeholder = st.empty()

    with placeholder.container():
        for i in range(1, 6):
            st.title(f"Background {i}")
            background_img = cv2.imread(f"{BGR_DIR}/background{i}.png")
            st.image(background_img, use_column_width=True, channels="BGR")

    st.sidebar.title("ITM News Generator")
    st.sidebar.text("(v1.0.0)")
    background = st.sidebar.radio(
        "Select a background",
        [
            "Background 1",
            "Background 2",
            "Background 3",
            "Background 4",
            "Background 5",
        ],
        key='background',
    )

    # create a button in sidebar
    generate_btn = st.sidebar.button("Generate news")

    # if the button is pressed run the code
    if generate_btn:
        placeholder.empty()

        if os.path.exists(RESULTS_DIR):
            shutil.rmtree(RESULTS_DIR)
            os.makedirs(RESULTS_DIR, exist_ok=True)

        bgr_img_path = f"{BGR_DIR}/{background.lower().replace(' ', '')}.png"

        with st.spinner("Generating news..."):
            data = crawl_news()
            for index, row in data.iterrows():
                # get the title and description
                title = row['title']
                description = row['description']
                time = row['time']

                # get the info image path
                img_path = row['image_path']
                info_img = cv2.imread(img_path)

                # read template image
                bgr_img = cv2.imread(bgr_img_path)
                merged_img = merge_info_img(bgr_img, info_img)
                merged_img = merge_text(title, description, merged_img)

                # save the result
                cv2.imwrite(f'{RESULTS_DIR}/{index}.png', merged_img)
    
        with placeholder.container():
            for index, row in data.iterrows():
                # get the title and description
                title = row['title']
                description = row['description']
                time = row['time']
                url = row['url']

                rs_img = cv2.imread(f'{RESULTS_DIR}/{index}.png')

                itm_content = (
                    title.upper()
                    + '<br>'
                    + '<br>'
                    + description
                    + '<br>'
                    + 'Nguồn VnExpress: '
                    + url
                    + '<br>'
                    + "-----"
                    + '<br>'
                    + "#ITMedia"
                    + '<br>'
                    + "#ITMNews"
                    + '<br>'
                    + "#ITMNewsGenerator"
                )
                st.title(title)
                st.text(time)
                st.markdown(itm_content, unsafe_allow_html=True)

                st.image(rs_img, use_column_width=True, channels="BGR")

                # create a button to download the image
                download_button_str = download_button(
                    open(f'{RESULTS_DIR}/{index}.png', 'rb').read(),
                    f'{index}.png',
                    'Download image',
                )
                st.markdown(download_button_str, unsafe_allow_html=True)

                # create a break line
                st.markdown("<br>", unsafe_allow_html=True)


if __name__ == "__main__":
    BGR_DIR = 'backgrounds'
    RESULTS_DIR = 'results'
    SAVE_POST_IMG_DIR = 'vnexpress_img'

    TITLE_FONT = ImageFont.truetype('fonts/OpenSans-ExtraBold.ttf', 72)
    TEXT_FONT = ImageFont.truetype('fonts/OpenSans-Regular.ttf', 54)
    SOURCE_FONT = ImageFont.truetype('fonts/OpenSans-ExtraBold.ttf', 54)
    WHITE_COLOR = (255, 255, 255)

    VNEXPRESS = 'https://vnexpress.net/so-hoa/cong-nghe'

    main()
