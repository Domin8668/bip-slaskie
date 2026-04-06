from bip_scraper.cities.base import CityScraper
from bip_scraper.cities.bytom import BytomScraper
from bip_scraper.cities.chorzow import ChorzowScraper
from bip_scraper.cities.dabrowa_gornicza import DabrowaGorniczaScraper
from bip_scraper.cities.gliwice import GliwiceScraper
from bip_scraper.cities.katowice import KatowiceScraper
from bip_scraper.cities.rudaslaska import RudaSlaskaScraper
from bip_scraper.cities.rybnik import RybnikScraper
from bip_scraper.cities.siemianowice import SiemianowiceScraper
from bip_scraper.cities.sosnowiec import SosnowiecScraper
from bip_scraper.cities.swietochlowice import SwietochlowiceScraper
from bip_scraper.cities.tychy import TychyScraper
from bip_scraper.cities.zabrze import ZabrzeScraper

ALL_CITY_SCRAPERS: tuple[CityScraper, ...] = (
    KatowiceScraper(),
    ChorzowScraper(),
    SwietochlowiceScraper(),
    SiemianowiceScraper(),
    GliwiceScraper(),
    SosnowiecScraper(),
    RudaSlaskaScraper(),
    ZabrzeScraper(),
    BytomScraper(),
    RybnikScraper(),
    TychyScraper(),
    DabrowaGorniczaScraper(),
)
