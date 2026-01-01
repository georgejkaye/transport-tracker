import sys
from datetime import date
from os import rename
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from stats.client import ApiClient


def get_duration_string(series: pd.Series) -> pd.Series:
    return (
        series.apply(lambda a: f"{int(a.seconds / 3600):02d}")  # type: ignore
        + ":"
        + series.apply(lambda a: f"{int(a.seconds % 3600 / 60):02d}")  # type: ignore
    )


def add_month_column(df: pd.DataFrame, datetime_column: str) -> pd.DataFrame:
    df["month"] = df[datetime_column].dt.month  # type: ignore
    return df


def round_datetime_column(
    df: pd.DataFrame, datetime_column: str, precision: str = "60s"
) -> pd.DataFrame:
    df[datetime_column] = df[datetime_column].dt.round(precision)  # type: ignore
    return df


def add_column_suffix(df: pd.DataFrame, column: str, suffix: str) -> pd.Series:
    return df[column].add_suffix(suffix)


def rename_columns(df: pd.DataFrame, columns: dict[str, str]) -> pd.DataFrame:
    return df.rename(columns=columns)


def loc(df: pd.DataFrame, index: Any) -> pd.DataFrame:
    return df.loc[:, index]  # type: ignore


def group_by(df: pd.DataFrame, by: str | list[str]) -> pd.DataFrame:
    return df.groupby(by)  # type: ignore


def get_count_frame(df: pd.DataFrame, by: str | list[str]) -> pd.DataFrame:
    return df.groupby(by).size().to_frame("count")  # type: ignore


def main(base_url: str):
    client = ApiClient(base_url)
    train_legs = client.get_user_train_legs_for_year(1, 2025)
    df = pd.DataFrame(train_legs)
    aggs = ["mean", "median", "min", "max"]
    aggs_dict = {"distance": aggs, "duration": aggs, "delay": aggs}
    train_df_total = df.agg(aggs_dict)
    train_df_total["distance"] = train_df_total["distance"].round(4)
    train_df_total = round_datetime_column(df, "duration")
    train_df_total["delay"] = train_df_total["delay"].round(1)
    train_df_total = add_month_column(train_df_total, "start_datetime")
    df_month = group_by(df[["month", "distance", "duration", "delay"]], "month").agg(
        {"month": "count", "distance": aggs, "duration": aggs, "delay": aggs}
    )
    df_month.loc[:, ("distance", "mean_str")] = df_month["distance"]["mean"].round(4)
    df_month.loc[:, ("distance", "median_str")] = df_month["distance"]["median"].round(
        4
    )
    df_month.loc[:, ("distance", "min_str")] = df_month["distance"]["min"].round(4)
    df_month.loc[:, ("distance", "max_str")] = df_month["distance"]["max"].round(4)
    df_month.loc[:, ("delay", "mean_str")] = (
        df_month["delay"]["mean"].round(0).astype("int")
    )
    df_month.loc[:, ("delay", "median_str")] = (
        df_month["delay"]["median"].round(0).astype("int")
    )
    df_month.loc[:, ("delay", "min_str")] = df_month["delay"]["min"].round(0)
    df_month.loc[:, ("delay", "max_str")] = df_month["delay"]["max"].round(0)
    df_month.loc[:, ("duration", "mean_str")] = get_duration_string(
        df_month["duration"]["mean"]
    )
    df_month.loc[:, ("duration", "median_str")] = get_duration_string(
        df_month["duration"]["median"]
    )
    df_month.loc[:, ("duration", "min_str")] = get_duration_string(
        df_month["duration"]["min"]
    )
    df_month.loc[:, ("duration", "max_str")] = get_duration_string(
        df_month["duration"]["max"]
    )
    df_train_month_strs = loc(
        df_month,
        (
            ["distance", "duration", "delay"],
            ["mean_str", "median_str", "min_str", "max_str"],
        ),
    )
    df_train_month_strs = df_train_month_strs.rename(
        columns={
            "mean_str": "mean",
            "median_str": "median",
            "min_str": "min",
            "max_str": "max",
        }
    )
    df_month_distance = add_column_suffix(df_train_month_strs, "distance", "_distance")
    df_month_duration = add_column_suffix(df_train_month_strs, "duration", "_duration")
    df_month_delay = add_column_suffix(df_train_month_strs, "delay", "_delay")

    train_df_month = (
        get_count_frame(df, "month")
        .join(df_month_distance)
        .join(df_month_duration)
        .join(df_month_delay)
    )
    bus_legs = client.get_user_bus_legs_for_year(1, 2025)
    bus_df = pd.DataFrame(bus_legs)
    bus_df = add_month_column(bus_df, "start_datetime")
    bus_df_total = bus_df.agg({"duration": aggs})
    bus_df_total = round_datetime_column(df, "duration")
    bus_df_month_agg = group_by(bus_df, "month").agg({"duration": aggs})
    bus_df_month_agg.loc[:, ("duration", "mean_str")] = get_duration_string(
        df_month["duration"]["mean"]
    )
    bus_df_month_agg.loc[:, ("duration", "median_str")] = get_duration_string(
        df_month["duration"]["median"]
    )
    bus_df_month_agg.loc[:, ("duration", "min_str")] = get_duration_string(
        df_month["duration"]["min"]
    )
    bus_df_month_agg.loc[:, ("duration", "max_str")] = get_duration_string(
        df_month["duration"]["max"]
    )

    bus_df_month_agg_duration = add_column_suffix(
        bus_df_month_agg, "duration", "_duration"
    )
    bus_df_month = (
        bus_df.groupby("month").size().to_frame("count").join(bus_df_month_agg_duration)
    )
    return (train_df_total, train_df_month, bus_df_total, bus_df_month)


if __name__ == "__main__":
    main(sys.argv[1])
