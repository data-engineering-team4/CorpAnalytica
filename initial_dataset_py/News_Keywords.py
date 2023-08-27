# 뉴스 키워드 및 3줄 요약 가져오기

import psycopg2
import json
import pandas as pd
from konlpy.tag import Okt, Kkma
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import normalize
import numpy as np
import threading

# 여기를 바꿔주세요!
news_article_csv_filename = 'news_article_2.csv'
news_keyword_csv_filename = 'news_keyword_2.csv'


df = pd.read_csv(news_article_csv_filename)
rows = df.values.tolist()
kkma = Kkma() 
okt = Okt()
#불용어제거
stopwords = ['머니투데이' , "연합뉴스", "데일리", "동아일보", "중앙일보", "조선일보", "기자","아", "휴", "아이구", "대한", "이번",
            "아이쿠", "아이고", "어", "나", "우리", "저희", "따라", "의해", "을", "를", "에", "의", "가", "기업", "트진", "위해",
            "지금", "말씀", "지난", "올해"]

tfidf = TfidfVectorizer()
cnt_vec = CountVectorizer()
graph_sentence = []
news_keyword_df = pd.DataFrame(columns = ['corpname','link','keywords','summary_sentence1','summary_sentence2','summary_sentence3'])


def split_sentences(text, start, end, result):
    sentences = kkma.sentences(text[start:end])
    result.extend(sentences)

def text2sentences(text):
    # 스레드 개수 설정
    num_threads = 4
    text_length = len(text)
    chunk_size = text_length // num_threads

    threads = []
    result = []

    # 스레드 생성 및 실행
    for i in range(num_threads):
        start = i * chunk_size
        end = (i + 1) * chunk_size if i != num_threads - 1 else text_length
        thread = threading.Thread(target=split_sentences, args=(text, start, end, result))
        thread.start()
        threads.append(thread)

    # 모든 스레드 종료 대기
    for thread in threads:
        thread.join()

    return result

def get_nouns(corpname, sentences):
    nouns = []
    for sentence in sentences:
        if sentence != '':
            nouns.append(' '.join([noun for noun in okt.nouns(str(sentence))
                                if noun not in stopwords and noun not in corpname and len(noun) > 1]))
    return nouns

def build_sent_graph(sentence):
    tfidf_mat = tfidf.fit_transform(sentence).toarray()
    graph_sentence = np.dot(tfidf_mat, tfidf_mat.T)
    return graph_sentence

def build_words_graph(sentence):
    cnt_vec_mat = normalize(cnt_vec.fit_transform(sentence).toarray().astype(float), axis=0)
    vocab = cnt_vec.vocabulary_
    return np.dot(cnt_vec_mat.T, cnt_vec_mat), {vocab[word] : word for word in vocab}

def get_ranks(graph, d=0.85): # d = damping factor
    A = graph
    matrix_size = A.shape[0]
    for id in range(matrix_size):
        A[id, id] = 0 # diagonal 부분을 0으로
        link_sum = np.sum(A[:,id]) # A[:, id] = A[:][id]
        if link_sum != 0:
            A[:, id] /= link_sum
        A[:, id] *= -d
        A[id, id] = 1

    B = (1-d) * np.ones((matrix_size, 1))
    ranks = np.linalg.solve(A, B) # 연립방정식 Ax = b
    return {idx: r[0] for idx, r in enumerate(ranks)}

def summarize(sent_num=3):
    summary = []
    index=[]
    for idx in sorted_sent_rank_idx[:sent_num]:
        index.append(idx)

    index.sort()
#     print(index)
    
    for idx in index:
        summary.append(sentences[idx])

    return summary

def keywords(word_num=20):

    keywords = []
    index=[]
    for idx in sorted_word_rank_idx[:word_num]:
        index.append(idx)

    #index.sort()
    for idx in index:
        keywords.append(idx2word[idx])

    return keywords

for row in rows:
    corpname = row[0]
    print(corpname)
    link = row[1]
    article = row[2]

    sentences = text2sentences(article)
    nouns = get_nouns(corpname, sentences)

    try:
        sent_graph = build_sent_graph(nouns)
    except ValueError:
        print(f"{link} : ValueError")
        continue

    words_graph, idx2word = build_words_graph(nouns)

    sent_rank_idx = get_ranks(sent_graph)  #sent_graph : sentence 가중치 그래프
    sorted_sent_rank_idx = sorted(sent_rank_idx, key=lambda k: sent_rank_idx[k], reverse=True)

    word_rank_idx = get_ranks(words_graph)
    sorted_word_rank_idx = sorted(word_rank_idx, key=lambda k: word_rank_idx[k], reverse=True)
    
    sum_sentence = summarize()
    sum_keyword = keywords()
    
    new_row = [corpname, link, sum_keyword, sum_sentence[0],sum_sentence[1],sum_sentence[2]]
    news_keyword_df.loc[len(news_keyword_df)] = new_row
    print("완료 : ", link)

news_keyword_df.to_csv(news_keyword_csv_filename, index=False, encoding='utf-8')