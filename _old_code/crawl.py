import os
import uuid

import pandas as pd
import requests
from bs4 import BeautifulSoup


DOWNLOAD_IMG_DIR = 'vnexpress_img'
os.makedirs(DOWNLOAD_IMG_DIR, exist_ok=True)

VNEXPRESS = 'https://vnexpress.net/so-hoa/cong-nghe'
response = requests.get(VNEXPRESS)

soup = BeautifulSoup(response.text, 'html.parser')

articles = soup.find_all('article', class_='item-news item-news-common thumb-left')
list_url = []
for article in articles:
    article_url = article.h2.a['href']
    list_url.append(article_url)
list_url = list(set(list_url))

df = pd.DataFrame(
    columns=['id', 'title', 'url', 'time', 'description', 'content', 'image_path']
)
for VNEXPRESS in list_url:
    try:
        response = requests.get(VNEXPRESS)
        soup = BeautifulSoup(response.text, 'html.parser')

        article_id = str(uuid.uuid4())

        title = soup.h1.text.strip()
        time = soup.find('span', class_='date').text.strip()

        # time will have format: like "Thứ sáu, 29/12/2023, 14:00 (GMT+7)"
        # we only need date
        time = time.split(',')[1].strip()

        # description = soup.find('p', class_='description').text.strip()
        description_tag = soup.find('p', class_='description')

        if description_tag.span:
            description_tag.span.decompose()

        description = description_tag.text.strip()
        content = soup.find('article', class_='fck_detail').text.strip()
        picture = soup.find('div', class_='fig-picture')
        try:
            image_url = picture.img['data-src']
            response = requests.get(image_url)
            image_path = DOWNLOAD_IMG_DIR + '/' + article_id + '.jpg'
            with open(image_path, 'wb') as f:
                f.write(response.content)

        except:
            image_path = None

        row = {
            'id': article_id,
            'title': title,
            'url': VNEXPRESS,
            'time': time,
            'description': description,
            'content': content,
            'image_path': image_path,
        }
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        print('Done: ', VNEXPRESS)
    except:
        print('Error: ', VNEXPRESS)


# drop row with empty image_path
df = df.dropna(subset=['image_path'])

print("Number of articles: ", len(df))
# save dataframe to csv file
df.to_csv('data/data.csv', index=False)
