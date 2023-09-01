from airflow import DAG
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.amazon.aws.transfers.s3_to_redshift import S3ToRedshiftOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.models import XCom

from datetime import datetime, timedelta
import pendulum
import logging
import pandas as pd
from konlpy.tag import Okt, Kkma
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import normalize
import numpy as np
import threading
#from plugins import slack_web_hook

local_timezone = pendulum.timezone("Asia/Seoul")



default_args = {
    'owner': 'JeeSeok',
    'retries': 1,
    'retry_delay': timedelta(minutes=2)
    #'on_failure_callback': slack_web_hook.on_failure_callback,
    #'on_success_callback': slack_web_hook.on_success_callback,
}

with DAG(
        dag_id='news_article_keyword_extract_DAG',
        start_date=datetime(2023, 8, 25, tzinfo=local_timezone),
        max_active_runs=1,
        default_args=default_args,
        catchup=False
) as dag:   

    # 네이버 뉴스 csv 파일로부터 링크를 읽어서 뉴스 키워드 추출
    def get_news_keyword_data_from_news(**kwargs):

        redshift_conn_id = 'Redshift_conn'
        logical_date_utc = datetime.now()
        logical_date_kst = (logical_date_utc - timedelta(days=1) + timedelta(hours=9)).strftime("%Y-%m-%d")
        logging.info(logical_date_kst)
        
        sql_query = f"""select na.corpname, na.link, art.article, art.id
                    from raw_data.naver_news as na, raw_data.news_article as art
                    where na.id = art.id
                    and na.pubdate like '{logical_date_kst}%';"""
        
        redshift_hook = PostgresHook(redshift_conn_id)
        connection = redshift_hook.get_conn()
        df = pd.read_sql_query(sql_query, connection)

        logging.info("redshift Connection Success")
        logging.info(df[:10])
        rows = df.values.tolist()
        #news_keyword_parquet_filename = "data/news_keyword/news_keyword_" + str(logical_date_kst.date()) + ".parquet"

        news_keyword_parquet_filename = f"data/news_keyword/news_keyword_{logical_date_kst}.parquet"        
        kwargs['ti'].xcom_push(key='news_keyword_parquet_filename', value=news_keyword_parquet_filename)
        logging.info(f"-- logical_date : {logical_date_kst} --\n-- 해당 날짜에서 뉴스 데이터를 가져옵니다. --")

        news_keyword_df = pd.DataFrame(columns = ['id','corpname','link','keywords','summary_sentence1','summary_sentence2','summary_sentence3'])
        news_keyword_list = []
        logging.info(f"총 {len(rows)}개의 기사")
        for row in rows:
            corpname = row[0]
            #print(corpname)
            link = row[1]
            article = row[2]
            sentences = text2sentences(article)
            nouns = get_nouns(corpname, sentences)
            sent_graph = build_sent_graph(nouns)
            words_graph, idx2word = build_words_graph(nouns)
            sent_rank_idx = get_ranks(sent_graph)  #sent_graph : sentence 가중치 그래프
            sorted_sent_rank_idx = sorted(sent_rank_idx, key=lambda k: sent_rank_idx[k], reverse=True)
            word_rank_idx = get_ranks(words_graph)
            sorted_word_rank_idx = sorted(word_rank_idx, key=lambda k: word_rank_idx[k], reverse=True)
            sum_sentence = summarize(sorted_sent_rank_idx, sentences)
            sum_keyword = keywords(sorted_word_rank_idx, idx2word)
            idx = row[3]

            new_row = [idx, corpname, link, sum_keyword, sum_sentence[0], sum_sentence[1], sum_sentence[2]]
            news_keyword_list.append(new_row)
            logging.info(f"{idx} 저장")

        news_keyword_df = pd.DataFrame(news_keyword_list, columns=['id','corpname', 'link', 'keywords', 'summary_sentence1', 'summary_sentence2', 'summary_sentence3'])
        news_keyword_df.to_parquet(news_keyword_parquet_filename, compression="gzip")
        logging.info(f"키워드 추출 완료")
            
    '''
    # 문장 분리하기
    def split_sentences(text, start, end, result):
        kkma = Kkma()
        sentences = kkma.sentences(text[start:end])
        result.extend(sentences)
    
    # 스레드 생성하여 문장 분리 실행
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
    '''
    def text2sentences(text):  
        kkma = Kkma()
        sentences = kkma.sentences(text)  #text일 때 문장별로 리스트 만듦
        for idx in range(0, len(sentences)):  #길이에 따라 문장 합침(위와 동일)
            if len(sentences[idx]) <= 10:
                sentences[idx-1] += (' ' + sentences[idx])
                sentences[idx] = ''
        return sentences
        #logging.info(sentences[:3])
    # 단어 추출
    def get_nouns(corpname, sentences):
        okt = Okt() 
        nouns = []
        stopwords = ['머니투데이' , "연합뉴스", "데일리", "동아일보", "중앙일보", "조선일보", "기자","아", "휴", "아이구", "대한", "이번",
                "아이쿠", "아이고", "어", "나", "우리", "저희", "따라", "의해", "을", "를", "에", "의", "가", "기업", "트진", "위해",
                "지금", "말씀", "지난", "올해"]
        for sentence in sentences:
            if sentence != '':
                nouns.append(' '.join([noun for noun in okt.nouns(str(sentence))
                                    if noun not in stopwords and noun not in corpname and len(noun) > 1]))
        return nouns

    # 문장 그래프 생성
    def build_sent_graph(sentence):
        tfidf = TfidfVectorizer()
        graph_sentence = []
        tfidf_mat = tfidf.fit_transform(sentence).toarray()
        graph_sentence = np.dot(tfidf_mat, tfidf_mat.T)
        return graph_sentence

    # 단어 그래프 생성
    def build_words_graph(sentence):
        cnt_vec = CountVectorizer()
        cnt_vec_mat = normalize(cnt_vec.fit_transform(sentence).toarray().astype(float), axis=0)
        vocab = cnt_vec.vocabulary_
        return np.dot(cnt_vec_mat.T, cnt_vec_mat), {vocab[word] : word for word in vocab}

    # 그래프 순위 매기기
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

    # 문장 3줄 요약
    def summarize(indexes, sentences, sent_num=3):
        summary = []
        index=[]
        for idx in indexes[:sent_num]:
            index.append(idx)

        index.sort()
    #     print(index)
        
        for idx in index:
            summary.append(sentences[idx])

        return summary

    # 키워드 20개 추출
    def keywords(indexes, idx2word, word_num=20):

        keyword = []
        index=[]
        for idx in indexes[:word_num]:
            index.append(idx)

        #index.sort()
        for idx in index:
            keyword.append(idx2word[idx])

        return keyword


    # s3에 parquet 파일 업로드
    def upload_parquet_to_s3(**kwargs):
        s3_hook = S3Hook(aws_conn_id='S3_conn')
        logging.info("S3 Connection Success")
        
        news_keyword_parquet_filename = kwargs['ti'].xcom_pull(task_ids='get_news_keyword_data_from_news_task', key='news_keyword_parquet_filename')
        
        s3_hook.load_file(
            filename=news_keyword_parquet_filename, 
            key=news_keyword_parquet_filename,
            bucket_name="de-4-3",
            replace=True
            )
        logging.info("Upload Parquet File Success")

    # Task


    get_news_keyword_data_from_news_task = PythonOperator(
        task_id='get_news_keyword_data_from_news_task',
        python_callable= get_news_keyword_data_from_news,
        provide_context=True,
        dag=dag
    )

    upload_news_keyword_parquet_to_s3_task = PythonOperator(
        task_id='upload_news_keyword_parquet_to_s3_task',
        python_callable= upload_parquet_to_s3,
        provide_context=True,
        dag=dag
    )

    news_keyword_s3_to_redshift_task = S3ToRedshiftOperator(
        task_id = 'news_keyword_s3_to_redshift_task',
        s3_bucket = "de-4-3",
        s3_key = "{{ ti.xcom_pull(task_ids='get_news_keyword_data_from_news_task', key='news_keyword_parquet_filename') }}",
        schema = "raw_data",
        table = "news_keyword",
        copy_options=["parquet", "IGNOREHEADER 1"],
        redshift_conn_id = "Redshift_conn",
        aws_conn_id = "S3_conn",    

        method = "UPSERT",
        upsert_keys = ["id"],
        dag = dag
    )

    trigger_wordcloud_dag_task = TriggerDagRunOperator(
        task_id='trigger_wordcloud_dag_task',
        trigger_dag_id='wordcloud_dag',
        execution_date="{{ execution_date }}"
    )

    trigger_DBT_dag_task = TriggerDagRunOperator(
        task_id='trigger_DBT_dag_task',
        trigger_dag_id='make_src_and_dbt_test_DAG',
        execution_date="{{ execution_date }}"
    )

    get_news_keyword_data_from_news_task >> upload_news_keyword_parquet_to_s3_task >> news_keyword_s3_to_redshift_task >> [trigger_wordcloud_dag_task, trigger_DBT_dag_task]