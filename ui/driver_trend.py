import pandas as pd
import seaborn as sns
import streamlit as st
from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from modules.inmemory_db import InmemoryDB


@st.cache_resource(ttl=60 * 10)
def create_driver_trend_plot(
    _db: InmemoryDB, list_driver: list[str], window: int = 1
) -> Figure:
    """Create driver trend through all career"""
    query = f"""
    SELECT 
        driver,
        position,
        constructor,
        season,
        round 
    FROM 
        race_result
    WHERE 
        driver IN ({','.join([f"'{driver}'" for driver in list_driver])})
    ORDER BY
        driver, season, round ASC
    """
    df = _db.execute_query(query)
    # ドライバーごとに時系列にソートしているため下記で問題ない
    df["position_mva"] = (
        df.groupby("driver")["position"].rolling(window, min_periods=1).mean().tolist()
    )
    # season, roundに一意の番号を割り振るためにseason, roundでソートしておく
    df.sort_values(by=["season", "round"], ascending=True, inplace=True)
    df["season_round_id"] = (
        pd.factorize(df[["season", "round"]].apply(tuple, axis=1))[0] + 1
    )

    fig, ax = plt.subplots()
    palette = sns.color_palette("coolwarm", df["driver"].nunique())
    for idx, driver in enumerate(df["driver"].unique()):
        df_driver = df.loc[df["driver"] == driver]
        if df["driver"].nunique() == 1:
            color = "skyblue"
        else:
            color = palette[idx]
        sns.lineplot(
            data=df_driver,
            x="season_round_id",
            y="position_mva",
            ax=ax,
            linestyle="-",
            label=driver,
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
