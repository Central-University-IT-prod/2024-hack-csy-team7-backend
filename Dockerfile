FROM python:3.9
#RUN pip install telebot
RUN pip install fastapi[standard]
RUN pip install psycopg2                              
COPY . .
CMD ["fastapi", "run", "main.py", "--port", "80"]
#CMD ["python", "bot.py"]