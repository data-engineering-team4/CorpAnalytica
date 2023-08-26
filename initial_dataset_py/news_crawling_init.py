# 뉴스 링크 csv 파일을 토대로 모든 기사를 크롤링

import requests
from bs4 import BeautifulSoup
import pandas as pd
import concurrent.futures
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import csv

# 바꿔주세요
naver_news_csv_filename = './news_data_2.csv'
news_article_csv_filename = './news_article_2.csv'


session = requests.Session()
retry = Retry(total = 3, connect=3, backoff_factor= 0.3)
session.mount('https://', HTTPAdapter(max_retries=retry))
session.mount('http://', HTTPAdapter(max_retries=retry))

# 네이버 뉴스 크롤링
def news_crawling_from_link(link):
    article = ""

    try:
        response = session.get(link)
        response.raise_for_status()  # HTTP 오류 체크
        soup = BeautifulSoup(response.text, "html.parser")

        if response.status_code != 200:
            return ""
        
        if "n.news.naver.com" in link:
            article_tag = soup.find("article")

        elif "www.enetnews.co.kr" in link:               
            article_tag = soup.find("article", id = "article-view-content-div")

        elif "www.itooza.com" in link:
            extract_tag = soup.find(class_="btn-wrap-01")
            extract_tag.extract()

            article_tag = soup.find("div", id = "article-body")

        elif "www.ggilbo.com" in link:
            article_tag = soup.find("article", id = "article-view-content-div")

        elif "www.cbci.co.kr" in link:
            # 제외할 태그들의 클래스 리스트
            exclude_classes = ['view-editors', 'view-copyright', 'figcaption']

            # 제외할 태그들을 반복문으로 제거
            for class_name in exclude_classes:
                extract_tags = soup.find_all(class_=class_name)
                
                for extract_tag in extract_tags:
                    extract_tag.extract()

            article_tag = soup.find("div", id = "article-view-content-div")
            
            # 끝의 두 개 p 태그 제거
            article_tag_p_extract = article_tag.find_all('p')

            if len(article_tag_p_extract) >= 2:
                article_tag_p_extract[-1].extract()
                article_tag_p_extract[-2].extract()

        elif "sports.news.naver.com" in link:
            # 제외할 태그들의 클래스 리스트
            exclude_classes = ['source', 'byline', 'reporter_area', 'copyright', 'categorize', 'promotion' ]

            # 제외할 태그들을 반복문으로 제거
            for class_name in exclude_classes:
                extract_tags = soup.find_all(class_=class_name)
                
                for extract_tag in extract_tags:
                    extract_tag.extract()

            article_tag = soup.find("div", id = "newsEndContents")

        elif "www.lcnews.co.kr" in link:
            article_tag = soup.find("article", id = "article-view-content-div")

        elif "www.wsobi.com" in link:
            # 인코딩 필요, 나중에 다른 언론사와 병합해도 되는지 확인필요함
            response = session.get(link)
            response.encoding = 'cp949'  
            soup = BeautifulSoup(response.text, "html.parser")

            article_tag = soup.find("div", id = "articleBody")

            article_tag_p_extract = article_tag.find_all('p')

            if len(article_tag_p_extract) >= 2:
                article_tag_p_extract[-1].extract()
                article_tag_p_extract[-2].extract()

        elif "www.gukjenews.com" in link:
            # 이미지 출처 제거
            extract_tags = soup.find_all('figcaption')
            for extract_tag in extract_tags:
                extract_tag.extract()

            article_tag = soup.find("article", id = "article-view-content-div")

        elif "www.thebell.co.kr" in link:
            extract_tag = soup.find(class_="tip mgb20")
            extract_tag.extract()

            article_tag = soup.find("div", id = "article_main")

        elif "https://www.etoday.co.kr" in link:
            extract_tag = soup.find('div', class_='relation_newslist')
            extract_tag.extract()
            
            article_tag = soup.select_one('.articleView')

        elif "www.newspim.com" in link:
            article_tag = soup.find('div', id='news-contents')

        elif "www.thekpm.com" in link:
            article_tag = soup.find('article', id='article-view-content-div')

        elif "news.mtn.co.kr" in link:
            extract_tag = soup.find('table', class_='article-photo-news center')
            extract_tag.extract()

            article_tag = soup.select_one('.news-content')

        elif "www.pinpointnews.co.kr" in link:
            article_tag = soup.find('article', id='article-view-content-div')

        elif "http://www.econonews.co.kr/" in link:
            article_tag = soup.find('article', id='article-view-content-div')

        elif "www.news2day.co.kr" in link:
            extract_tag = soup.find('figure', id='id_div_main')
            extract_tag.extract()

            article_tag = soup.select_one('.view_con.cf') 

        elif "http://www.thebigdata.co.kr/" in link:
            article_tag = soup.find('div', class_='txt_article')

        else:
            return ""

        article = article_tag.text

    except requests.exceptions.RequestException as e:
        print(e)
        print(f"Request Failed / 링크 : {link}")

    except AttributeError as e:
        print(f"{link}에는 해당 태그를 찾을 수 없습니다. / {e}")
    
    except Exception as e:
        print(f"기타 에러 / 링크 : {link} / 에러 : {e}")

    article = article.replace('\n', '').strip()    
    return article

# 링크 처리
def process_link(line):
    corpname = line[1]
    link = line[3]
    pubdate = line[5]
    article = news_crawling_from_link(link)

    if len(article) < 1:
        print(f"{corpname}의 뉴스 데이터를 가져올 수 없습니다. 링크 : {link}")
        return None

    news_dic = {
        'corpname': corpname,
        'link': link,
        'article': article,
        'pubdate': pubdate
    }
    
    print(f"{corpname}의 뉴스 {line[2]} 저장")
    return news_dic


with open(naver_news_csv_filename, 'r', encoding='utf-8') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)  # 헤더 무시

        total_news_article_list = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(process_link, csv_reader))

        for result in results:
            if result:
                total_news_article_list.append(result)
            print("적재 완료")

        df = pd.DataFrame(total_news_article_list)
        df.to_csv(news_article_csv_filename, index=False, encoding='utf-8')