import base64
from .models import *
from io import BytesIO
from matplotlib import pyplot as plt
from wordcloud import WordCloud
from django.http import HttpResponse
import io

def get_graph():
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    graph = base64.b64encode(image_png)
    graph = graph.decode('utf-8')
    buffer.close()
    return graph


def get_wordcloud(keyword_list, **kwargs):
    plt.switch_backend('AGG') # 화면에 플롯팅 방지
    plt.figure(figsize=(10, 4))


    font_path = "./static/fonts/BMDOHYEON.ttf"

    # 등수별로 단어와 그 등수를 딕셔너리로 매핑
    ranked_word_dict = {word: len(keyword_list) - rank + 1 for rank, word in enumerate(keyword_list, start=1)}

    # 워드클라우드 생성
    wordcloud = WordCloud(
        width=800, height=400, 
        font_path=font_path, 
        background_color='white'
    ).generate_from_frequencies(ranked_word_dict)

    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')

    plt.tight_layout()
    img = get_graph()

    return img