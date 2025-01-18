FROM python:3.12.3

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

CMD ["python", "interface.py"]
#CMD python ${SCRIPT_TO_RUN:-interface.py}