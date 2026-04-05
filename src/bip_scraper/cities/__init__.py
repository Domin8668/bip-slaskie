from bip_scraper.cities.base import CityScraper
from bip_scraper.cities.chorzow import ChorzowScraper
from bip_scraper.cities.katowice import KatowiceScraper
from bip_scraper.cities.siemianowice import SiemianowiceScraper
from bip_scraper.cities.swietochlowice import SwietochlowiceScraper

ALL_CITY_SCRAPERS: tuple[CityScraper, ...] = (
    KatowiceScraper(),
    ChorzowScraper(),
    SwietochlowiceScraper(),
    SiemianowiceScraper(),
)
