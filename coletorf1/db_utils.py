import os

from pymongo import MongoClient
from dotenv import load_dotenv


load_dotenv()

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27018"
)


def get_database():
    """
    Conecta ao MongoDB e retorna o banco openf1_data.
    """
    client = MongoClient(MONGO_URI)

    # Testa a conexão
    client.admin.command("ping")

    return client["openf1_data"]


def get_years(db):
    """
    Retorna os anos disponíveis na collection sessions.
    """
    years = db.sessions.distinct("year")

    return sorted(years, reverse=True)


def get_sessions_by_year(db, year):
    """
    Retorna as sessões de corrida disponíveis para o ano selecionado.
    """

    sessions = list(
        db.sessions.find(
            {
                "year": year,
                "session_type": "Race"
            },
            {
                "_id": 0
            }
        ).sort("date_start", 1)
    )

    return sessions


def get_session(db, session_key):
    """
    Retorna os dados de uma sessão específica.
    """

    return db.sessions.find_one(
        {
            "session_key": session_key
        },
        {
            "_id": 0
        }
    )


def get_drivers_by_session(db, session_key):
    """
    Retorna os pilotos participantes de uma sessão.
    """

    drivers = list(
        db.drivers.find(
            {
                "session_key": session_key
            },
            {
                "_id": 0
            }
        ).sort("driver_number", 1)
    )

    return drivers


def get_laps_by_drivers(
    db,
    session_key,
    driver_numbers
):
    """
    Retorna os dados de voltas dos pilotos selecionados.
    """

    laps = list(
        db.laps.find(
            {
                "session_key": session_key,
                "driver_number": {
                    "$in": driver_numbers
                },
                "lap_duration": {
                    "$ne": None
                }
            },
            {
                "_id": 0,
                "session_key": 1,
                "driver_number": 1,
                "lap_number": 1,
                "lap_duration": 1
            }
        ).sort(
            [
                ("lap_number", 1),
                ("driver_number", 1)
            ]
        )
    )

    return laps