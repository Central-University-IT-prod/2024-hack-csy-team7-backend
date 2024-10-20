from fastapi import FastAPI, HTTPException, Request, APIRouter
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import psycopg2
import os
import uvicorn
import datetime
from typing import Union
from statistics import median


class QueueInf(BaseModel):
    queueName: str
    timePerUser: int


class TgUserName(BaseModel):
    tg_name: str


class UserId(BaseModel):
    id_user: int


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
# postgres_database = os.getenv("POSTGRES_DATABASE", "queue")
# postgres_username = os.getenv("POSTGRES_USERNAME", "postgres")
# postgres_password = os.getenv("POSTGRES_PASSWORD", "{{sensitive data}}")
# postgres_host = os.getenv("POSTGRES_HOST", "localhost")
# postgres_port = os.getenv("POSTGRES_PORT", "5432")

postgres_database = os.getenv("POSTGRES_DATABASE", "queue")
postgres_username = os.getenv("POSTGRES_USERNAME", "postgres")
postgres_password = os.getenv("POSTGRES_PASSWORD", "{{sensitive data}}")
postgres_host = os.getenv("POSTGRES_HOST", "{{sensitive data}}")
postgres_port = os.getenv("POSTGRES_PORT", "5432")


# Роут для регистрации
@app.post("/queue/create", status_code=200)
async def register(profile: QueueInf):
    try:
        name = profile.queueName
        time = profile.timePerUser
        print(name, time)

        if len(name) == 0:
            raise HTTPException(status_code=400, detail="Name is too short")
        if time <= 0:
            raise HTTPException(status_code=400, detail="Wrong time format")

        conn = psycopg2.connect(
            database=postgres_database,
            user=postgres_username,
            password=postgres_password,
            host=postgres_host,
            port=postgres_port
        )

        with conn.cursor() as curs:
            # Создание таблицы, если не существует
            # curs.execute('''
            #     DROP TABLE queues''')
            curs.execute('''
                CREATE TABLE IF NOT EXISTS queues (
                    id SERIAL PRIMARY KEY, 
                    name VARCHAR(200) NOT NULL, 
                    time INTEGER NOT NULL
                )
            ''')
            conn.commit()

            # Вставка данных
            values = {'name': name, 'time': time}
            curs.execute(
                "INSERT INTO queues (name, time) VALUES (%(name)s, %(time)s)",
                values
            )
            conn.commit()
            curs.execute('SELECT name FROM queues')
            logins = [i[0] for i in curs.fetchall()]
        print(name, time)
        print(logins, 11)
        profile_data = {"queueName": name, "timePerUser": time}
        return profile_data

    except Exception as ex:
        print(ex)
        raise HTTPException(status_code=400, detail="Wrong profile data")


@app.post("/queue/start", status_code=200)
async def start(profile: TgUserName):
    print(88)
    tg_name = profile.tg_name
    conn = psycopg2.connect(
        database=postgres_database,
        user=postgres_username,
        password=postgres_password,
        host=postgres_host,
        port=postgres_port
    )

    with conn.cursor() as curs:
        # Создание таблицы, если не существует
        # curs.execute('''
        #     DROP TABLE users''')
        curs.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY, 
                        tg_name VARCHAR(32) UNIQUE NOT NULL
                    )
                ''')
        conn.commit()
        print(6767)

        values = {'tg_name': tg_name}
        curs.execute(
            "SELECT tg_name FROM users WHERE tg_name = \'%s\'" % (tg_name,))
        all_tg_names = curs.fetchall()
        if not all_tg_names:
            curs.execute(
                "INSERT INTO users (tg_name) VALUES (%(tg_name)s)",
                values
            )
            conn.commit()

        curs.execute('''
                    CREATE TABLE IF NOT EXISTS queue_user (
                        id SERIAL PRIMARY KEY, 
                        id_queue INTEGER NOT NULL,
                        id_user INTEGER NOT NULL,
                        time_come TIMESTAMP, 
                        duration INTERVAL, 
                        active BOOLEAN DEFAULT true
                    )
                ''')
        conn.commit()
        # values = {'id_queue': 1, 'id_user': 3}
        # curs.execute(
        #     "INSERT INTO queue_user (id_queue, id_user) VALUES (%(id_queue)s, %(id_user)s)",
        #     values
        # )
        # conn.commit()
        curs.execute('''
                    SELECT count(id_user) FROM queue_user WHERE active = true
                    ''')
        if curs:
            active_people_amount = curs.fetchone()[0]
        else:
            active_people_amount = 0
        curs.execute('''
                    SELECT duration FROM queue_user WHERE active = false
                    ''')
        durations = curs.fetchall()
        durations = sorted([durs[0].total_seconds() for durs in curs.fetchall()])
        if len(durations) > 2:
            durations = sorted([durs[0].total_seconds() for durs in durations])
            time_per_user = median(durations)
            print(durations, time_per_user)
        else:
            curs.execute('''
                SELECT name, time FROM queues WHERE id = 1
                ''')
            name_and_time = curs.fetchone()
            queue_name = name_and_time[0]
            time_per_person = name_and_time[1]
        time_prediction = time_per_person * active_people_amount

    print({'queue_name': queue_name,
            'active_people_amount': active_people_amount,
            'time_prediction': time_prediction})
    return {'queue_name': queue_name,
            'active_people_amount': active_people_amount,
            'time_prediction': time_prediction}


@app.post("/queue/user/add", status_code=200)
async def add(profile: TgUserName):
    print(88)
    tg_name = profile.tg_name
    conn = psycopg2.connect(
        database=postgres_database,
        user=postgres_username,
        password=postgres_password,
        host=postgres_host,
        port=postgres_port
    )

    with conn.cursor() as curs:
        # Создание таблицы, если не существует
        # curs.execute('''
        #     DROP TABLE users''')
        curs.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY, 
                        tg_name VARCHAR(32) UNIQUE NOT NULL
                    )
                ''')
        conn.commit()
        print(6767)

        values = {'tg_name': tg_name}
        curs.execute(
            "SELECT id FROM users WHERE tg_name = \'%s\'" % (tg_name,))
        id_user = curs.fetchone()[0]

        curs.execute('''
                    CREATE TABLE IF NOT EXISTS queue_user (
                        id SERIAL PRIMARY KEY, 
                        id_queue INTEGER NOT NULL,
                        id_user INTEGER NOT NULL,
                        time_come TIMESTAMP, 
                        duration INTERVAL, 
                        active BOOLEAN DEFAULT true
                    )
                ''')
        conn.commit()

        curs.execute(
            "SELECT id FROM queue_user WHERE id_queue = 1 AND id_user = \'%s\' AND active = true" % (id_user,))

        if not curs.fetchall():
            values = {'id_queue': 1, 'id_user': id_user}
            curs.execute(
                "INSERT INTO queue_user (id_queue, id_user) VALUES (%(id_queue)s, %(id_user)s)",
                values
            )
            conn.commit()

        curs.execute('''
                    SELECT count(id_user) FROM queue_user WHERE active = true
                    ''')
        if curs:
            active_people_amount = curs.fetchone()[0]
        else:
            active_people_amount = 0
        curs.execute('''
                    SELECT duration FROM queue_user WHERE active = false
                    ''')
        durations = curs.fetchall()

        if len(durations) > 2:
            durations = sorted([durs[0].total_seconds() for durs in curs.fetchall()])
            time_per_user = median(durations)
            print(durations, time_per_user)
        else:
            curs.execute('''
                SELECT name, time FROM queues WHERE id = 1
                ''')
            name_and_time = curs.fetchone()
            queue_name = name_and_time[0]
            time_per_person = name_and_time[1]
        time_prediction = time_per_person * active_people_amount

    return {'queue_name': queue_name,
            'active_people_amount': active_people_amount,
            'time_prediction': time_prediction,
            'id_user': id_user}


@app.post("/queue/user/update", status_code=200)
async def update(profile: TgUserName):
    print(88)
    tg_name = profile.tg_name
    conn = psycopg2.connect(
        database=postgres_database,
        user=postgres_username,
        password=postgres_password,
        host=postgres_host,
        port=postgres_port
    )

    with conn.cursor() as curs:
        # Создание таблицы, если не существует
        # curs.execute('''
        #     DROP TABLE users''')
        curs.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY, 
                        tg_name VARCHAR(32) UNIQUE NOT NULL
                    )
                ''')
        conn.commit()
        print(6767)

        values = {'tg_name': tg_name}
        curs.execute(
            "SELECT id FROM users WHERE tg_name = \'%s\'" % (tg_name,))
        id_user = curs.fetchone()[0]

        curs.execute('''
                    CREATE TABLE IF NOT EXISTS queue_user (
                        id SERIAL PRIMARY KEY, 
                        id_queue INTEGER NOT NULL,
                        id_user INTEGER NOT NULL,
                        time_come TIMESTAMP, 
                        duration INTERVAL, 
                        active BOOLEAN DEFAULT true
                    )
                ''')
        conn.commit()

        curs.execute(
            "SELECT id FROM queue_user WHERE id_queue = 1 AND id_user = \'%s\' AND active = true" % (id_user,))

        id_queue_user = curs.fetchall()

        if not id_queue_user:
            is_in_queue = False
        else:
            is_in_queue = True

        curs.execute('''
                    SELECT count(id_user) FROM queue_user WHERE active = true AND id < \'%s\'
                    ''' % (id_queue_user[0][0]))
        if curs:
            active_people_amount = curs.fetchone()[0] + 1
        else:
            active_people_amount = 1
        curs.execute('''
                    SELECT duration FROM queue_user WHERE active = false
                    ''')
        durations = curs.fetchall()

        if len(durations) > 2:
            durations = sorted([durs[0].total_seconds() for durs in durations])
            time_per_user = median(durations)
            print(durations, time_per_user)
        else:
            curs.execute('''
                SELECT name, time FROM queues WHERE id = 1
                ''')
            name_and_time = curs.fetchone()
            queue_name = name_and_time[0]
            time_per_person = name_and_time[1]
        time_prediction = time_per_person * active_people_amount

    return {'queue_name': queue_name,
            'active_people_amount': active_people_amount,
            'time_prediction': time_prediction,
            'id_user': id_user,
            'is_in_queue': is_in_queue}


@app.post("/queue/user/remove", status_code=200)
async def remove(profile: TgUserName):
    print(88)
    tg_name = profile.tg_name
    conn = psycopg2.connect(
        database=postgres_database,
        user=postgres_username,
        password=postgres_password,
        host=postgres_host,
        port=postgres_port
    )

    with conn.cursor() as curs:
        # Создание таблицы, если не существует
        # curs.execute('''
        #     DROP TABLE users''')
        curs.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY, 
                        tg_name VARCHAR(32) UNIQUE NOT NULL
                    )
                ''')
        conn.commit()
        print(6767)

        values = {'tg_name': tg_name}
        curs.execute(
            "SELECT id FROM users WHERE tg_name = \'%s\'" % (tg_name,))
        id_user = curs.fetchone()[0]

        curs.execute('''
                    CREATE TABLE IF NOT EXISTS queue_user (
                        id SERIAL PRIMARY KEY, 
                        id_queue INTEGER NOT NULL,
                        id_user INTEGER NOT NULL,
                        time_come TIMESTAMP, 
                        duration INTERVAL, 
                        active BOOLEAN DEFAULT true
                    )
                ''')
        conn.commit()

        curs.execute(
            "SELECT id FROM queue_user WHERE id_queue = 1 AND id_user = \'%s\' AND active = true" % (id_user,))

        in_queue_id = curs.fetchall()
        print('in_queue_fetchall', in_queue_id)

        if not in_queue_id:
            return {'status': False}
        else:
            in_queue_id = in_queue_id[0][0]

        curs.execute('''
                    DELETE FROM queue_user WHERE id = \'%s\'
                    ''' % (in_queue_id,))
        conn.commit()
        return {'status': True}


@app.post("/queue/user/delete", status_code=200)
async def delete(profile: UserId):
    print(88)
    id_user = profile.id_user
    print(id_user)
    conn = psycopg2.connect(
        database=postgres_database,
        user=postgres_username,
        password=postgres_password,
        host=postgres_host,
        port=postgres_port
    )

    with conn.cursor() as curs:
        # Создание таблицы, если не существует
        # curs.execute('''
        #     DROP TABLE users''')
        curs.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY, 
                        tg_name VARCHAR(32) UNIQUE NOT NULL
                    )
                ''')
        conn.commit()
        print(6767)

        curs.execute('''
                    CREATE TABLE IF NOT EXISTS queue_user (
                        id SERIAL PRIMARY KEY, 
                        id_queue INTEGER NOT NULL,
                        id_user INTEGER NOT NULL,
                        time_come TIMESTAMP, 
                        duration INTERVAL, 
                        active BOOLEAN DEFAULT true
                    )
                ''')
        conn.commit()

        curs.execute(
            "SELECT id FROM queue_user WHERE id_queue = 1 AND id_user = \'%s\' AND active = true" % (id_user,))

        in_queue_id = curs.fetchall()
        print('in_queue_fetchall', in_queue_id)

        if not in_queue_id:
            return {'status': False}
        else:
            in_queue_id = in_queue_id[0][0]

        curs.execute('''
                    DELETE FROM queue_user WHERE id = \'%s\'
                    ''' % (in_queue_id,))
        conn.commit()
        return {'status': True}


@app.post("/queue/user/pass", status_code=200)
async def delete(profile: UserId):
    print(88)
    id_user = profile.id_user
    conn = psycopg2.connect(
        database=postgres_database,
        user=postgres_username,
        password=postgres_password,
        host=postgres_host,
        port=postgres_port
    )

    with conn.cursor() as curs:
        # Создание таблицы, если не существует
        # curs.execute('''
        #     DROP TABLE users''')
        curs.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY, 
                        tg_name VARCHAR(32) UNIQUE NOT NULL
                    )
                ''')
        conn.commit()
        print(6767)

        curs.execute('''
                    CREATE TABLE IF NOT EXISTS queue_user (
                        id SERIAL PRIMARY KEY, 
                        id_queue INTEGER NOT NULL,
                        id_user INTEGER NOT NULL,
                        time_come TIMESTAMP, 
                        duration INTERVAL, 
                        active BOOLEAN DEFAULT true
                    )
                ''')
        conn.commit()

        curs.execute(
            "SELECT id FROM queue_user WHERE id_queue = 1 AND id_user = \'%s\' AND active = true" % (id_user,))

        in_queue_id_time = curs.fetchall()
        print('in_queue_fetchall', in_queue_id_time)

        if not in_queue_id_time:
            return {'status': False}
        else:
            in_queue_id = in_queue_id_time[0][0]

        curs.execute('UPDATE queue_user SET active = false WHERE id = \'%s\'' % (in_queue_id,))
        conn.commit()

        time_now = datetime.datetime.now()
        # time_come = in_queue_id_time[0][1]
        # dur = time_now - time_come

        curs.execute('UPDATE queue_user SET time_come = \'%s\' WHERE id = \'%s\'' % (time_now, in_queue_id))
        conn.commit()

        curs.execute(
            "SELECT id FROM queue_user WHERE id < \'%s\'" % (in_queue_id,))

        ids_before = curs.fetchall()
        print('idsbef', ids_before)

        if ids_before:
            id_prev = ids_before[-1][0]
            print('prev', id_prev)
            curs.execute(
                "SELECT time_come FROM queue_user WHERE id_queue = 1 AND id = \'%s\' AND active = false" % (id_prev,))

            time_come_prev = curs.fetchall()[0][0]
            print(time_come_prev)

            duration = time_now - time_come_prev
            curs.execute('UPDATE queue_user SET duration = \'%s\' WHERE id = \'%s\'' % (duration, id_prev))
            conn.commit()

        curs.execute(
            "SELECT id FROM queue_user WHERE active = true")
        if not curs.fetchall():
            curs.execute(
                "SELECT time FROM queues WHERE id = 1")
            average_time = curs.fetchall()[0][0]
            print(average_time)
            curs.execute('UPDATE queue_user SET duration = \'%s\' WHERE id = \'%s\'' % (average_time, in_queue_id))
            conn.commit()

        return {'status': True}


@app.post("/queue/users", status_code=200)
async def delete(profile: UserId):
    print(88)
    conn = psycopg2.connect(
        database=postgres_database,
        user=postgres_username,
        password=postgres_password,
        host=postgres_host,
        port=postgres_port
    )

    with conn.cursor() as curs:
        # Создание таблицы, если не существует
        # curs.execute('''
        #     DROP TABLE users''')
        curs.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY, 
                        tg_name VARCHAR(32) UNIQUE NOT NULL
                    )
                ''')
        conn.commit()
        print(6767)

        curs.execute('''
                    CREATE TABLE IF NOT EXISTS queue_user (
                        id SERIAL PRIMARY KEY, 
                        id_queue INTEGER NOT NULL,
                        id_user INTEGER NOT NULL,
                        time_come TIMESTAMP, 
                        duration INTERVAL, 
                        active BOOLEAN DEFAULT true
                    )
                ''')
        conn.commit()

        curs.execute(
            "SELECT id_user FROM queue_user WHERE active = true")

        all_people = curs.fetchall()
        people_list = [idd[0] for idd in all_people]

        return {'users': people_list}


# Запуск приложения
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

