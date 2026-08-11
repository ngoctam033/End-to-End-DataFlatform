FROM apache/airflow:3.1.6

USER root

# CẤU HÌNH PHIÊN BẢN SPARK
# QUAN TRỌNG: Phải khớp hoàn toàn với phiên bản trong container spark-worker
# Nếu spark-worker dùng 3.5.5, hãy đổi thành 3.5.5
# ENV SPARK_VERSION=3.5.5
# ENV HADOOP_VERSION=3

# # Cài đặt Java và Spark binaries từ internet
# # Thêm procps để khắc phục lỗi "ps: command not found"
# RUN apt-get update \
#     && apt-get install -y --no-install-recommends procps wget ca-certificates \
#     && wget -q https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.10%2B7/OpenJDK17U-jdk_x64_linux_hotspot_17.0.10_7.tar.gz -P /tmp/ \
#     && mkdir -p /usr/lib/jvm/java-17-openjdk-amd64 \
#     && tar -xzf /tmp/OpenJDK17U-jdk_x64_linux_hotspot_17.0.10_7.tar.gz -C /usr/lib/jvm/java-17-openjdk-amd64 --strip-components=1 \
#     && rm /tmp/OpenJDK17U-jdk_x64_linux_hotspot_17.0.10_7.tar.gz \
#     && apt-get autoremove -yqq --purge \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# RUN wget -q https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz -P /tmp/ \
#     && tar -xzf /tmp/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz -C /opt/ \
#     && mv /opt/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION} /opt/spark \
#     && rm /tmp/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz

# # Download JARs directly
# RUN wget -q https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.8.1/iceberg-spark-runtime-3.5_2.12-1.8.1.jar -P /opt/spark/jars/ && \
#     wget -q https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar -P /opt/spark/jars/ && \
#     wget -q https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar -P /opt/spark/jars/ && \
#     wget -q https://repo1.maven.org/maven2/org/postgresql/postgresql/42.6.0/postgresql-42.6.0.jar -P /opt/spark/jars/

# ENV SPARK_HOME=/opt/spark
# ENV PATH="$SPARK_HOME/bin:$PATH"
# ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

USER airflow

# Copy requirements
COPY --chown=airflow:0 airflow/requirements.txt /tmp/requirements.txt

# Cài đặt qua internet
RUN pip install --no-cache-dir -r /tmp/requirements.txt