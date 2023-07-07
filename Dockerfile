FROM nixos/nix

RUN nix-channel --add https://channels.nixos.org/nixos-23.05 nixpkgs && \
    nix-channel --update

WORKDIR /app

ENV DOCKER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIPENV_CLEAR=1

COPY Pipfile.lock shell.nix ./
RUN nix-shell --run "true"

RUN mkdir -p data/boards data/cache data/download && \
    touch data/blacklist.txt data/clips.txt data/clips_replay.txt data/db.json
VOLUME [ "/app/data" ]

COPY LICENSE Makefile *.py ./
COPY html ./html/
COPY static ./static/
COPY templates ./templates/
COPY data/ranks ./data/ranks/

EXPOSE 8000
ENTRYPOINT [ "nix-shell", "--run" ]
CMD [ "pipenv run uvicorn main:app --host 0.0.0.0" ]
