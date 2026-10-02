FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN useradd --create-home --uid 1000 mockapi
WORKDIR /app
COPY --chown=mockapi:mockapi main.py ./
COPY --chown=mockapi:mockapi mockapi/ mockapi/
COPY --chown=mockapi:mockapi examples/ examples/

USER mockapi
EXPOSE 8080

ENTRYPOINT ["python", "main.py"]
CMD ["examples/api.json", "--host", "0.0.0.0", "--port", "8080"]
