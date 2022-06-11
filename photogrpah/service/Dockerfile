FROM ubuntu

RUN apt-get update -y
RUN apt-get install -y zip python3 pip
COPY . .
RUN pip install -r requirements.txt

CMD ["python3", "server.py", "--log"]