from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import psycopg2
import os
from fastapi import APIRouter

router = APIRouter()
app = FastAPI()

# Модель данных для валидации запроса
class Profile(BaseModel):
    name: str
    age: int

# Настройки подключения к PostgreSQL
postgres_database = os.getenv("POSTGRES_DATABASE", "queue")
postgres_username = os.getenv("POSTGRES_USERNAME", "postgres")
postgres_password = os.getenv("POSTGRES_PASSWORD", "{{sensitive data}}")
postgres_host = os.getenv("POSTGRES_HOST", "localhost")
postgres_port = os.getenv("POSTGRES_PORT", "5432")


# Роут для регистрации
@app.post("/azy/auth/register", status_code=201)
async def register(profile: Profile):
    try:
        name = profile.name
        age = profile.age

        if len(name) == 0:
            raise HTTPException(status_code=400, detail="Name is too short")
        if age <= 0:
            raise HTTPException(status_code=400, detail="Wrong age format")

        conn = psycopg2.connect(
            database=postgres_database,
            user=postgres_username,
            password=postgres_password,
            host=postgres_host,
            port=postgres_port
        )

        with conn.cursor() as curs:
            # Создание таблицы, если не существует
            curs.execute('''
                CREATE TABLE IF NOT EXISTS queues (
                    id SERIAL PRIMARY KEY, 
                    name VARCHAR(30) UNIQUE NOT NULL, 
                    age INTEGER NOT NULL
                )
            ''')
            conn.commit()

            # Вставка данных
            values = {'name': name, 'age': age}
            curs.execute(
                "INSERT INTO queues (name, age) VALUES (%(name)s, %(age)s)",
                values
            )
            conn.commit()
        print(name, age)
        profile_data = {"name": name, "age": age}
        return profile_data

    except Exception as ex:
        print(ex, 2)
        raise HTTPException(status_code=400, detail="Wrong profile data")


# Роуты для работы с элементами
@app.get("/azy/primery_api/{element_id}")
async def get_element(element_id: int):
    return {
        'id': element_id,
        'сообщение': f'Настоящий API запрос возвращает информацию об отдельной сущности {element_id}',
        'метод': "GET"
    }

@app.put("/azy/primery_api/{element_id}")
async def update_element(element_id: int, request: Request):
    body = await request.json()
    return {
        'id': element_id,
        'сообщение': f'Данный API запрос обновляет отдельную сущность {element_id}',
        'метод': "PUT",
        'body': body
    }

@app.delete("/azy/primery_api/{element_id}")
async def delete_element(element_id: int):
    return {
        'id': element_id,
        'сообщение': f'Настоящий API запрос удаляет отдельную сущность {element_id}',
        'метод': "DELETE"
    }
