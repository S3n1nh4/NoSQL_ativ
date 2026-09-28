import os
import requests
from pymongo import MongoClient
from dotenv import load_dotenv


# ========================================================
# 1. Carregando variáveis de ambiente
# ========================================================

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openf1.org/v1")

SESSION_KEY = int(os.getenv("SESSION_KEY", "9159"))
MEETING_KEY = int(os.getenv("MEETING_KEY", "1219"))
YEAR = int(os.getenv("YEAR", "2023"))


# ========================================================
# 2. Função de conexão ao MongoDB
# ========================================================

def get_mongo_connection():
    """
    Conecta ao MongoDB e retorna o banco de dados.
    """
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

        # Testa a conexão
        client.admin.command("ping")

        db = client["openf1_data"]

        print("[INFO] Conexão com MongoDB realizada com sucesso.")

        return db

    except Exception as e:
        print(f"[ERRO] Falha ao conectar ao MongoDB: {e}")
        raise


# ========================================================
# 3. Função para buscar dados da API
# ========================================================

def fetch_data(endpoint: str, params: dict) -> list:
    """
    Faz uma requisição GET para a API OpenF1.

    Args:
        endpoint (str): Nome do endpoint.
        params (dict): Parâmetros da consulta.

    Returns:
        list: Lista de registros retornados pela API.
    """

    url = f"{API_BASE_URL}/{endpoint}"

    try:
        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        print(
            f"[INFO] {len(data)} registros obtidos "
            f"de '{endpoint}'."
        )

        return data

    except requests.RequestException as e:
        print(
            f"[ERRO] Falha ao buscar dados de "
            f"'{endpoint}': {e}"
        )

        return []


# ========================================================
# 4. Função para salvar dados no MongoDB
# ========================================================

def save_to_collection(
    db,
    data: list,
    collection_name: str,
    unique_keys: list
):
    """
    Insere ou atualiza registros no MongoDB.

    Utiliza update_one com upsert=True para evitar
    duplicação dos dados em execuções posteriores.

    Args:
        db: Banco de dados MongoDB.
        data (list): Dados recebidos da API.
        collection_name (str): Nome da collection.
        unique_keys (list): Campos que formam a chave única.
    """

    collection = db[collection_name]

    processados = 0

    for record in data:

        query = {
            key: record.get(key)
            for key in unique_keys
        }

        # Verifica se todos os campos da chave existem
        if any(value is None for value in query.values()):
            print(
                f"[WARN] Registro ignorado por "
                f"faltar chave única: {record}"
            )
            continue

        try:
            collection.update_one(
                query,
                {"$set": record},
                upsert=True
            )

            processados += 1

        except Exception as e:
            print(
                f"[ERRO] Falha ao salvar registro "
                f"na collection '{collection_name}': {e}"
            )

    print(
        f"[INFO] {processados} registros processados "
        f"na collection '{collection_name}'."
    )


# ========================================================
# 5. Fluxo Principal
# ========================================================

def main():
    db = get_mongo_connection()

    # ====================================================
    # Passo 1: Buscar todas as sessões do ano
    # ====================================================
    sessions_data = fetch_data("sessions", {"year": YEAR})

    save_to_collection(
        db,
        sessions_data,
        "sessions",
        ["session_key"]
    )

    # ====================================================
    # Passo 2 e 3:
    # Para cada sessão, buscar pilotos e voltas
    # ====================================================
    total_sessoes = len(sessions_data)

    for contador, session in enumerate(sessions_data, start=1):

        session_key = session.get("session_key")

        if not session_key:
            continue

        print(
            f"\n[INFO] Processando sessão "
            f"{contador}/{total_sessoes} - session_key={session_key}"
        )

        # -----------------------------------------------
        # Pilotos
        # -----------------------------------------------
        drivers_data = fetch_data(
            "drivers",
            {"session_key": session_key}
        )

        save_to_collection(
            db,
            drivers_data,
            "drivers",
            ["session_key", "driver_number"]
        )

        # -----------------------------------------------
        # Voltas
        # -----------------------------------------------
        laps_data = fetch_data(
            "laps",
            {"session_key": session_key}
        )

        save_to_collection(
            db,
            laps_data,
            "laps",
            [
                "session_key",
                "driver_number",
                "lap_number"
            ]
        )

    print("\n========================================")
    print("[SUCESSO] Coleta de todas as sessões finalizada!")
    print("========================================")


# ========================================================
# 6. Execução direta do script
# ========================================================
if __name__ == "__main__":
    main()