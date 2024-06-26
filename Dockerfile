# syntax=docker/dockerfile:1
FROM python:3.12 AS build

RUN apt update && apt install -y graphviz && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

WORKDIR /build

ADD build/build.tar .

RUN poetry build

RUN pip install $(ls ./dist/*.whl)[docs]

WORKDIR /build/docs

RUN make html

FROM python:3.12 AS app

ENV INSIDE_DOCKER 1  # Used in python to know if it is running inside a docker

RUN ssh-keygen -t ecdsa -b 521 -C "Insecure key for fuzzungus ssh monitor" -N '' -f /root/.ssh/id_ecdsa

RUN apt update && apt install -y graphviz postgresql && rm -rf /var/lib/apt/lists/*

WORKDIR /app/docker_html_docs

COPY --from=build /build/docs/_build/html .

WORKDIR /app

COPY --from=build /build/dist .

RUN pip install *.whl

# COPY --chmod=500 docker_entrypoint.sh .
# The previous line didn't work on old docker version
# Workaround : run the chmod separately

COPY docker_entrypoint.sh .

RUN chmod 500 docker_entrypoint.sh

CMD ["/app/docker_entrypoint.sh"]
