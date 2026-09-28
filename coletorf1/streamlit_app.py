import streamlit as st
import pandas as pd

from db_utils import (
    get_database,
    get_years,
    get_sessions_by_year,
    get_session,
    get_drivers_by_session,
    get_laps_by_drivers
)


# ========================================================
# Configuração da página
# ========================================================

st.set_page_config(
    page_title="OpenF1 Data Explorer",
    page_icon="🏎️",
    layout="wide"
)


# ========================================================
# Conexão com MongoDB
# ========================================================

@st.cache_resource
def load_database():
    return get_database()


try:
    db = load_database()

except Exception as e:
    st.error(
        f"Não foi possível conectar ao MongoDB: {e}"
    )
    st.stop()


# ========================================================
# Título
# ========================================================

st.title("🏎️ OpenF1 Data Explorer")

st.write(
    "Explore e compare dados de sessões, pilotos e voltas "
    "armazenados no MongoDB."
)


# ========================================================
# Barra lateral
# ========================================================

st.sidebar.header("Filtros")


years = get_years(db)

if not years:
    st.warning(
        "Nenhum ano foi encontrado na collection sessions."
    )
    st.stop()


selected_year = st.sidebar.selectbox(
    "Selecione o ano",
    years
)


# ========================================================
# Seleção da corrida
# ========================================================

sessions = get_sessions_by_year(
    db,
    selected_year
)

if not sessions:
    st.warning(
        "Nenhuma sessão de corrida encontrada para "
        f"{selected_year}."
    )
    st.stop()


def session_label(session):
    """
    Define o texto exibido no seletor de corridas.
    """

    name = session.get(
        "session_name",
        "Corrida"
    )

    country = session.get(
        "country_name",
        ""
    )

    return f"{name} - {country}"


selected_session = st.sidebar.selectbox(
    "Selecione a Corrida",
    sessions,
    format_func=session_label
)


session_key = selected_session["session_key"]


# ========================================================
# Informações da sessão
# ========================================================

session = get_session(
    db,
    session_key
)

st.subheader("Informações da sessão")


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "País",
        session.get(
            "country_name",
            "N/A"
        )
    )


with col2:

    st.metric(
        "Circuito",
        session.get(
            "circuit_short_name",
            "N/A"
        )
    )


with col3:

    date = session.get(
        "date_start",
        "N/A"
    )

    if isinstance(date, str):
        date = date[:10]

    st.metric(
        "Data",
        date
    )


# ========================================================
# Pilotos
# ========================================================

st.subheader("Comparação de pilotos")


drivers = get_drivers_by_session(
    db,
    session_key
)


if not drivers:

    st.warning(
        "Nenhum piloto encontrado para esta sessão."
    )

    st.stop()


driver_options = {}


for driver in drivers:

    number = driver.get(
        "driver_number"
    )

    name = driver.get(
        "full_name"
    )

    if not name:

        name = driver.get(
            "name_acronym",
            f"Piloto {number}"
        )

    driver_options[
        f"{number} - {name}"
    ] = number


selected_driver_names = st.multiselect(
    "Selecione os pilotos para comparar",
    list(driver_options.keys())
)


if not selected_driver_names:

    st.info(
        "Selecione pelo menos um piloto para "
        "visualizar o gráfico."
    )

    st.stop()


selected_driver_numbers = [
    driver_options[name]
    for name in selected_driver_names
]


# ========================================================
# Dados das voltas
# ========================================================

laps = get_laps_by_drivers(
    db,
    session_key,
    selected_driver_numbers
)


if not laps:

    st.warning(
        "Não foram encontrados dados de voltas "
        "para os pilotos selecionados."
    )

    st.stop()


# ========================================================
# DataFrame
# ========================================================

df = pd.DataFrame(laps)


# Adiciona o nome do piloto
driver_names = {}

for driver in drivers:

    number = driver.get(
        "driver_number"
    )

    name = driver.get(
        "full_name"
    )

    if not name:
        name = driver.get(
            "name_acronym",
            f"Piloto {number}"
        )

    driver_names[number] = name


df["driver_name"] = df[
    "driver_number"
].map(driver_names)


# ========================================================
# Gráfico
# ========================================================

st.subheader(
    "Tempo de volta por número da volta"
)


chart_df = df.pivot(
    index="lap_number",
    columns="driver_name",
    values="lap_duration"
)


st.line_chart(chart_df)


# ========================================================
# Tabela
# ========================================================

with st.expander(
    "Ver tabela de dados"
):

    st.dataframe(
        df[
            [
                "lap_number",
                "driver_number",
                "driver_name",
                "lap_duration"
            ]
        ],
        use_container_width=True
    )