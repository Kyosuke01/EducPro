FROM python:3.12-slim

RUN groupadd --system educpro \
    && useradd --system --gid educpro --create-home --home-dir /home/educpro educpro

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY app.py ./app.py
COPY db ./db

RUN chown -R educpro:educpro /app

USER educpro

EXPOSE 5000

CMD ["python", "app.py"]
