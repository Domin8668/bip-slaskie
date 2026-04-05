from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class CitySlug(StrEnum):
    KATOWICE = "katowice"
    CHORZOW = "chorzow"
    SWIETOCHLOWICE = "swietochlowice"
    SIEMIANOWICE = "siemianowice"
    GLIWICE = "gliwice"
    SOSNOWIEC = "sosnowiec"
    RUDASLASKA = "rudaslaska"
    ZABRZE = "zabrze"
    BYTOM = "bytom"
    RYBNIK = "rybnik"
    TYCHY = "tychy"
    DABROWAG = "dabrowa-gornicza"


class LegalAct(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    stable_id: str = Field(min_length=8)
    title: str = Field(min_length=1)
    published_at: datetime
    source_url: HttpUrl


class CitySnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    city: CitySlug
    collected_at: datetime
    acts: list[LegalAct]


class DailySnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_date: date
    generated_at: datetime
    cities: dict[CitySlug, CitySnapshot]


class CityDiff(BaseModel):
    model_config = ConfigDict(extra="forbid")

    city: CitySlug
    previous_count: int = Field(ge=0)
    current_count: int = Field(ge=0)
    new_count: int = Field(ge=0)
    new_acts: list[LegalAct]


class DailyDiffReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_date: date
    compared_to_date: date | None = None
    total_new: int = Field(ge=0)
    city_diffs: list[CityDiff]
