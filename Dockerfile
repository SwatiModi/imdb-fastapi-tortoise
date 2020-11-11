FROM python:3.8.6
LABEL maintainer="Swati Modi"
RUN mkdir -p /usr/src/imdb
WORKDIR /usr/src/imdb
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port 8000