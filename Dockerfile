FROM python:3.8

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

#RUN pip install requests
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
EXPOSE 8000
CMD ["uvicorn", "main:app"]

#CMD [ "python3.8", "./teste.py" ]
