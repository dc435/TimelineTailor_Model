FROM pytorch/pytorch:1.13.1-cuda11.6-cudnn8-runtime

WORKDIR /

RUN apt-get update && apt-get install -y git

RUN pip3 install --upgrade pip
ADD requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 install torch --extra-index-url https://download.pytorch.org/whl/cu116

WORKDIR /app

ADD src/. .

WORKDIR /app/model
COPY download.py .
ARG ADDRESS
RUN python -c "from download import download_files; download_files('$ADDRESS')"

WORKDIR /

EXPOSE 8000

CMD python3 -u app/app.py