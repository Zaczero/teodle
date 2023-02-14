FROM python:3.10.8-slim

ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/* && \
    pip install \
    --no-cache-dir \
    --disable-pip-version-check \
    pipenv \
    yt-dlp

WORKDIR /app

RUN groupadd --gid 1000 appuser && \
    useradd --gid 1000 --uid 1000 --create-home --no-log-init appuser && \
    chown 1000:1000 .

USER 1000:1000

COPY --chown=1000:1000 Pipfile* .
RUN pipenv install --deploy --ignore-pipfile && \
    pipenv --clear

COPY --chown=1000:1000 *.py ./
COPY --chown=1000:1000 ranks ./ranks/
COPY --chown=1000:1000 static ./static/
COPY --chown=1000:1000 templates ./templates/
RUN python -m compileall .

VOLUME ["/app/download"]
ENTRYPOINT ["pipenv", "run", "uvicorn", "main:app"]
CMD ["--host", "0.0.0.0"]
