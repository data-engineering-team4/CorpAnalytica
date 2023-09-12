<div align='center'>
<img src="https://github.com/data-engineering-team4/CorpAnalytica/assets/123959802/f7402690-9035-44bf-a646-3c87815bb3b2" width='350' >
</div>

# CorpAnalytica
### 뉴스 기사를 기반으로 한 기업 분석 웹사이트 구축
<br>

## ✔️ 프로젝트 개요
### 목적
수 많은 국내 기업들 중 내가 관심있는 기업의 최근 동향을 해당 기업의 뉴스 기사를 통해 추출한 키워드와 주식 데이터로 파악할 수 있다.
<br>

### 개발 기간
- 23.08.07 ~ 23.09.05 (4주)

### 팀원 소개 및 역할
|  이름  | 역할 | GitHub | 
| :---: | :---: | :--- |
| 김승언 | AWS 환경 세팅 및 인프라 구성, 데이터 수집 및 적재, ETL, 백엔드 | [@SikHyeya](https://github.com/SikHyeya) |
| 김선호 | 데이터 수집 및 적재, ETL, ELT, 데이터 모니터링, 프론트엔드, 백엔드 | [@sunhokim1457](https://github.com/sunhokim1457) |
| 김지석 | AWS 환경 세팅 및 인프라 구성, 데이터 수집 및 적재, ETL, ELT, 자연어처리 | [@plays0708](https://github.com/plays0708) |
<br>

## ⚒️ Tech Stack
| Field | Stack |
|:---:|:---:|
| Database | <img src="https://img.shields.io/badge/amazonredshift-8C4FFF?style=for-the-badge&logo=amazonredshift&logoColor=white"><img src="https://img.shields.io/badge/amazons3-569A31?style=for-the-badge&logo=amazons3&logoColor=white"> ||
| ETL & ELT | <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white"/> <img src="https://img.shields.io/badge/Airflow-017CEE?style=for-the-badge&logo=Apache%20Airflow&logoColor=white"/><img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white"><img src="https://img.shields.io/badge/dbt-FF694B?style=for-the-badge&logo=dbt&logoColor=white"> ||
| Data monitoring | <img src="https://img.shields.io/badge/prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white"> <img src="https://img.shields.io/badge/grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white"> <img src="https://img.shields.io/badge/slack-4A154B?style=for-the-badge&logo=slack&logoColor=white">||
| Web | <img src="https://img.shields.io/badge/django-092E20?style=for-the-badge&logo=django&logoColor=white"> ||
| CI/CD | <img src="https://img.shields.io/badge/githubactions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white"> <img src="https://img.shields.io/badge/amazonec2-FF9900?style=for-the-badge&logo=amazonec2&logoColor=white">||
| Tools | <img src="https://img.shields.io/badge/github-181717?style=for-the-badge&logo=github&logoColor=white"> <img src="https://img.shields.io/badge/figma-F24E1E?style=for-the-badge&logo=figma&logoColor=white"> <img src="https://img.shields.io/badge/notion-000000?style=for-the-badge&logo=notion&logoColor=white">||
<br>

## 🏛️ Architecture
![Architecture](https://github.com/data-engineering-team4/CorpAnalytica/assets/123959802/baef5021-01e5-404a-b8f8-122fe94b99e5)
<br>

## 🧩 ERD
![ERD](https://github.com/data-engineering-team4/CorpAnalytica/assets/123959802/315832b5-ae54-4f98-a394-85dec4bd0ebc)
<br>

## 🎁 결과 화면
<img width="1680" alt="스크린샷 2023-09-04 오후 4 32 40" src="https://github.com/SikHyeya/CorpAnalytica/assets/123959802/d8d1f5e0-573c-47a8-981e-a378784f4f75">
<img width="1680" alt="스크린샷 2023-09-04 오후 4 33 10" src="https://github.com/SikHyeya/CorpAnalytica/assets/123959802/c981ffa1-7849-4b07-8af9-2e70ef2bc9df">
<img width="1680" alt="스크린샷 2023-09-04 오후 4 33 15" src="https://github.com/SikHyeya/CorpAnalytica/assets/123959802/f55322df-51b9-4d63-8083-58fd2f9e5c5e">
<br>

## 💊 TO DO
- 주식데이터 kafka를 사용하여 실시간 처리 후 적재하여 인사이트 도출
- 컨테이너 오케스트레이션 시스템 도입
- EFK 스택 도입하여 로그데이터 수집을 통한 인사이트 도출
<br>


