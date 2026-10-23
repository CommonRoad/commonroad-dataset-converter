FROM python:3.10 AS build

RUN pip install poetry
RUN poetry self add poetry-plugin-export
WORKDIR /app

COPY crdata /app/crdata
COPY pyproject.toml /app/
COPY README.md /app/

RUN poetry export -o requirements.txt --without-hashes
RUN poetry build -f wheel

FROM python:3.10-slim AS app

RUN apt-get update && apt-get install -y gcc cmake git

COPY --from=build /app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt && rm /app/requirements.txt

COPY --from=build /app/dist/*.whl /app/
RUN pip install /app/*.whl && rm /app/*.whl

ENTRYPOINT ["crconvert"]
CMD ["--help"]
