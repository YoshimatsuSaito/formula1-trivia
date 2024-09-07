import pandas as pd
import seaborn as sns
import streamlit as st
from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from modules.inmemory_db import InmemoryDB


@st.cache_data(ttl=60 * 60 * 24, show_spinner=True)
def _cached_constructor_position(_db: InmemoryDB) -> pd.DataFrame:
    """Create constructor posiotn table"""
    query = """
    SELECT 
        SUM(points) AS constructor_point,
        constructor,
        season,
        round,
        ROW_NUMBER() OVER (PARTITION BY season, round ORDER BY SUM(points) DESC) AS constructor_position
    FROM 
        race_result
    GROUP BY
        constructor, season, round
    ORDER BY
        constructor ASC, season ASC, round ASC
    """
    df = _db.execute_query(query)
    return df


@st.cache_resource(ttl=60 * 10)
def create_constructor_trend_plot(
    _db: InmemoryDB, list_constructor: list[str], window: int = 1
) -> Figure:
    df = _cached_constructor_position(_db=_db)
    df = df.loc[df["constructor"].isin(list_constructor)].reset_index(drop=True)
    # コンストラクターごとに時系列にソートしているため下記で問題ない
    df["position_mva"] = (
        df.groupby("constructor")["constructor_position"]
        .rolling(window, min_periods=1)
        .mean()
        .tolist()
    )
    # season, roundに一意の番号を割り振るためにseason, roundでソートしておく
    df.sort_values(by=["season", "round"], ascending=True, inplace=True)
    df["season_round_id"] = (
        pd.factorize(df[["season", "round"]].apply(tuple, axis=1))[0] + 1
    )

    fig, ax = plt.subplots()
    palette = sns.color_palette("coolwarm", df["constructor"].nunique())
    for idx, constructor in enumerate(df["constructor"].unique()):
        df_constructor = df.loc[df["constructor"] == constructor]
        if df["constructor"].nunique() == 1:
            color = "skyblue"
        else:
            color = palette[idx]
        sns.lineplot(
            data=df_constructor,
            x="season_round_id",
            y="position_mva",
            ax=ax,
            linestyle="-",
            label=constructor,
            color=color,
        )
    ax.set_xlabel("Year", fontsize=14)
    ax.set_ylabel("Race Position", fontsize=14)

    # 下記が成り立つためには、season, roundでソートされている必要がある
    first_rounds = df.drop_duplicates("season", keep="first")
    ticks = first_rounds["season_round_id"].tolist()
    labels = first_rounds["season"].astype(str).tolist()

    ax.set_xticks(ticks)
    ax.set_xticklabels(labels, rotation=45)
    ax.set_yticks(range(1, 21))
    ax.set_ylim(1, 20)

    ax.invert_yaxis()
    plt.tight_layout()

    return fig
