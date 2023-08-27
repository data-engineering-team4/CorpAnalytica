# Use an official Airflow image as the base
ARG AIRFLOW_VERSION=2.6.2
FROM apache/airflow:${AIRFLOW_VERSION}

# Install Java and set JAVA_HOME
RUN apt-get update && \
    apt-get install -y default-jre && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME environment variable
ENV JAVA_HOME=/usr/lib/jvm/java-1.8-openjdk

# Set environment variables
ENV AIRFLOW_HOME=/opt/airflow

USER root
COPY config/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY config/airflow.cfg ${AIRFLOW_HOME}/airflow.cfg
COPY dags ${AIRFLOW_HOME}/dags
COPY plugins ${AIRFLOW_HOME}/plugins

RUN chown -R airflow: ${AIRFLOW_HOME}

ENV PYTHONPATH ${AIRFLOW_HOME}

USER airflow

ADD requirements.txt .
RUN pip install apache-airflow==${AIRFLOW_VERSION} -r requirements.txt 

EXPOSE 8080 5555 8793

WORKDIR ${AIRFLOW_HOME}
ENTRYPOINT ["/entrypoint.sh"]
