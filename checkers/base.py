from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Offer:
    checker_name: str
    key: str
    country: str
    category: str
    name: str
    cpu: str
    ram: str
    disk: str
    network: str
    price: float
    currency: str
    order_url: str


class BaseChecker(ABC):
    name: str
    display_name: str

    @abstractmethod
    async def fetch_available(self) -> list[Offer]:
        ...
