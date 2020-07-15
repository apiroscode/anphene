from dataclasses import dataclass
from typing import List


@dataclass
class CourierService:
    cost: int
    service: str = ""
    description: str = ""
    etd: str = ""


@dataclass
class Courier:
    code: str
    name: str
    services: List[CourierService]


@dataclass
class WaybillStatus:
    status: str = ""
    receiver: str = ""
    date: str = ""


@dataclass
class WaybillHistory:
    date: str = ""
    description: str = ""
    city: str = ""


@dataclass
class Waybill:
    status: WaybillStatus
    histories: List[WaybillHistory]
