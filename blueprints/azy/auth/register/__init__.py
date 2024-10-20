from fastapi import FastAPI, HTTPException, Request, APIRouter
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import psycopg2
import os
import uvicorn
from typing import Union


class Profile(BaseModel):
    name: str
    age: int


app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Можете ограничить конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройки JSON
app.json_encoders = {
    'ascii': False,  # Для поддержки Unicode
}

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
        print(name, age)

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
        print(ex)
        raise HTTPException(status_code=400, detail="Wrong profile data")


# Запуск приложения
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)

