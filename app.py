import os

import streamlit as st
from dotenv import load_dotenv

from modules.inmemory_db import InmemoryDB
from modules.util import load_config
from ui.driver_trend import create_driver_trend_plot
from ui.constructor_trend import create_constructor_trend_plot

load_dotenv()

BUCKET_NAME = os.environ.get("BUCKET_NAME")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

if BUCKET_NAME is None or AWS_ACCESS_KEY_ID is None or AWS_SECRET_ACCESS_KEY is None:
    BUCKET_NAME = st.secrets["BUCKET_NAME"]
    AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
    AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]

DICT_CONFIG = load_config("./config/config.yml")


@st.cache_resource(ttl=60 * 60, show_spinner=True)
def _cached_inmemory_db() -> InmemoryDB:
    db = InmemoryDB(bucket_name=BUCKET_NAME)
    db.create_inmemory_db(dict_csv_key=DICT_CONFIG["s3_grandprix_result_data_key"])
    return db


@st.cache_data(ttl=60 * 60 * 24, show_spinner=True)
def _cached_driver_list(_db: InmemoryDB) -> list[str]:
    df = _db.execute_query(
        """
            SELECT
                DISTINCT driver
            FROM
                race_result    
        """
    )
    return df["driver"].tolist()


@st.cache_data(ttl=60 * 60 * 24, show_spinner=True)
def _cached_constructor_list(_db: InmemoryDB) -> list[str]:
    df = _db.execute_query(
        """
            SELECT
                DISTINCT constructor
            FROM
                race_result    
        """
    )
    df["constructor_alias"] = df["constructor"].replace(
        DICT_CONFIG["constructor_mapping"]
    )
    df.sort_values(by="constructor_alias", inplace=True)
    return df["constructor_alias"].unique().tolist()


# Cache
# Setup duckdb
db = _cached_inmemory_db()
# Get driver list
list_driver = _cached_driver_list(_db=db)
list_constructor = _cached_constructor_list(_db=db)

st.title("Formula 1 Trivia")
st.markdown(
    "This dashboard allows Formula 1 fans to explore various statistics as a hobby. New statistics will be added periodically."
)

genre = st.selectbox(label="Select a data", options=["driver", "constructor"], index=0)

st.markdown("---")

# Driver trend
if genre == "driver":
    st.subheader("Driver Trends")
    list_selected_driver = st.multiselect(
        "Select or type drivers",
        list_driver,
        default=["Max Verstappen", "Lewis Hamilton", "Fernando Alonso"],
    )

    if len(list_driver) > 0:
        dict_fig = dict()
        for window in [1, 5, 10, 20]:
            dict_fig[window] = create_driver_trend_plot(
                _db=db, list_driver=list_selected_driver, window=window
            )

        window_chosen = st.radio(
            "Select the moving average window size for positions",
            [1, 5, 10, 20],
            index=2,
            horizontal=True,
        )
        st.pyplot(dict_fig[window_chosen])
    else:
        st.error("Select a driver")

if genre == "constructor":
    st.subheader("Constructor Trends")
    list_selected_constructor = st.multiselect(
        "Select or type constructors",
        list_constructor,
        default=["Ferrari"],
    )

    if len(list_constructor) > 0:
        dict_fig = dict()
        for window in [1, 5, 10, 20]:
            dict_fig[window] = create_constructor_trend_plot(
                _db=db,
                list_constructor=list_selected_constructor,
                window=window,
                dict_constructor_mapping=DICT_CONFIG["constructor_mapping"],
            )

        window_chosen = st.radio(
            "Select the moving average window size for positions",
            [1, 5, 10, 20],
            index=2,
            horizontal=True,
        )
        st.pyplot(dict_fig[window_chosen])
    else:
        st.error("Select a constructor")
