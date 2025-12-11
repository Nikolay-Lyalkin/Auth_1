FROM python:3.11.9

RUN apt-get update && \
    apt-get install -y locales gettext && \
    sed -i '/en_US.UTF-8/s/^# //' /etc/locale.gen && \
    locale-gen

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN pip install --no-cache-dir poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root

COPY . .

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Указываем entrypoint
ENTRYPOINT ["/bin/bash", "/docker-entrypoint.sh"]