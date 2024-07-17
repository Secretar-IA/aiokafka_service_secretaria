FROM public.ecr.aws/docker/library/python:3.10.14-slim-bookworm

ENV POETRY_VIRTUALENVS_CREATE=0
# dont write pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# dont buffer to stdout/stderr
ENV PYTHONUNBUFFERED 1

WORKDIR /src

RUN pip install poetry==1.8.3
COPY pyproject.toml poetry.lock ./
RUN poetry lock
RUN poetry install --no-root

COPY ./aiokafka_manager_service ./aiokafka_manager_service
COPY ./tests ./tests

ENV PYTHONPATH=/src

#CMD ["tail", "-f", "/dev/null"]
CMD ["bash"]