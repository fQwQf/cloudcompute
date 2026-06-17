ARG SPARK_IMAGE=docker.m.daocloud.io/apache/spark:3.5.0
FROM ${SPARK_IMAGE}

ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ARG POSTGRES_JDBC_URL=https://maven.aliyun.com/repository/public/org/postgresql/postgresql/42.7.4/postgresql-42.7.4.jar

USER root
RUN pip3 install --no-cache-dir -i ${PIP_INDEX_URL} py4j==0.10.9.7 \
    && mkdir -p /opt/spark/jars/postgresql \
    && curl -fsSL -o /opt/spark/jars/postgresql/postgresql.jar ${POSTGRES_JDBC_URL}

COPY job.py /opt/cloudcostlab/job.py

USER spark
ENV PYTHONPATH=/opt/spark/python
ENV SPARK_HOME=/opt/spark
ENTRYPOINT ["/opt/spark/bin/spark-submit", "--jars", "/opt/spark/jars/postgresql/postgresql.jar", "/opt/cloudcostlab/job.py"]
