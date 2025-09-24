# syntax=docker/dockerfile:1

FROM python:3.11-alpine

RUN adduser -D -s /bin/sh coderunner
USER coderunner
WORKDIR /workspace

ENV PATH="/home/coderunner/.local/bin:${PATH}"

COPY docker/code_runner/requirements.txt ./container-requirements.txt
RUN pip install --user --no-cache-dir -r container-requirements.txt && \
    rm container-requirements.txt

CMD ["python", "-c", "print('Container ready')"]
