import base64
from .models import *
from io import BytesIO
from matplotlib import pyplot as plt
from wordcloud import WordCloud
import FinanceDataReader as fdr
from datetime import datetime, timedelta
import matplotlib.font_manager as fm
import matplotlib
import requests

matplotlib.use('Agg') # plt 오류 방지

# 이미지 로드에 버퍼 사용
def get_graph():
    buffer = BytesIO()
    plt.savefig(buffer, format='png', transparent=True)
    buffer.seek(0)
    image_png = buffer.getvalue()
    graph = base64.b64encode(image_png)
    graph = graph.decode('utf-8')
    buffer.close()
    return graph


# 워드클라우드 생성(detail_view)
def get_wordcloud(keyword_list, **kwargs):
    fig = plt.figure()

    plt.figure(figsize=(10, 4))

    font_path = "./static/fonts/BMDOHYEON.ttf"

    # 등수별로 단어와 그 등수를 딕셔너리로 매핑
    ranked_word_dict = {word: len(keyword_list) - rank + 1 for rank, word in enumerate(keyword_list, start=1)}

    # 워드클라우드 생성
    wordcloud = WordCloud(
        width=1200, height=400, 
        max_words=17,
        prefer_horizontal=1,
        max_font_size=200,
        font_path=font_path, 
        background_color=None,
        mode = "RGBA",
        colormap = 'PuBu' 
    ).generate_from_frequencies(ranked_word_dict)

    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.tight_layout()

    img = get_graph()
    plt.close(fig)
    return img

# 주식 그래프 생성(detail_view)
def get_stock_graph(stock_code):

    font_path = "./static/fonts/BMDOHYEON.ttf"
    font_prop = fm.FontProperties(fname=font_path, size=12)

    fig, ax = plt.subplots(figsize=(10, 6))  # 그래프 크기 조정
    plt.style.use('ggplot')  # 스타일 설정 (ggplot 스타일 사용)

    logical_date_now = datetime.now()
    logical_date_6months_ago = (logical_date_now - timedelta(days=180))
    df = fdr.DataReader(stock_code, logical_date_6months_ago.strftime("%Y-%m-%d"), logical_date_now.strftime("%Y-%m-%d"))
    df['Close'].plot(ax=ax, linewidth=3, color='blue', label=stock_code)  # 그래프 라인 스타일링

    ax.set_xlabel('날짜(월)', fontsize=11, fontproperties=font_prop)  # x 축 레이블 추가
    ax.set_ylabel('주가', fontsize=11, fontproperties=font_prop)  # y 축 레이블 추가

    img = get_graph()

    return img

# 홈 화면에 S3 워드클라우드 로딩(home_view)
def get_s3_image_url(base_url, max_attempts=5):
    img_date = datetime.now() - timedelta(days=1)

    for _ in range(max_attempts):
        img_url = base_url + img_date.strftime("%Y-%m-%d") + ".png"
        response = requests.get(img_url)

        if response.status_code == 200:
            return img_url

        img_date -= timedelta(days=1)

    return None