import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

from ... import Courier, CourierService, Waybill, WaybillHistory, WaybillStatus
from ....plugins import PluginType
from ....plugins.base_plugin import BasePlugin, ConfigurationTypeField
from ....site.models import SiteSettings
from ....users.models import Address


@dataclass
class PluginConfig:
    fetch_shipping_cost: bool
    fetch_waybill: bool
    params: Dict[str, Any]


DESTINATION_TYPE = "subdistrict"
URL_COST = "https://pro.rajaongkir.com/api/cost"
URL_WAYBILL = "https://pro.rajaongkir.com/api/waybill"


class RajaOngkirPlugin(BasePlugin):
    PLUGIN_ID = "anphene.shipping.raja_ongkir"
    PLUGIN_NAME = "Raja Ongkir"
    PLUGIN_DESCRIPTION = "For fetching courier info and cost."
    PLUGIN_TYPE = PluginType.SHIPPING
    DEFAULT_ACTIVE = False

    DEFAULT_CONFIGURATION = [
        {"name": "api_key", "value": ""},
        {"name": "courier", "value": "[]"},
        {"name": "fetch_shipping_cost", "value": False},
        {"name": "fetch_waybill", "value": False},
    ]
    CONFIG_STRUCTURE = {
        "api_key": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Provide raja ongkir API key.",
            "label": "API key",
        },
        "courier": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Choose couriers for display on checkout page.",
            "label": "Courier",
        },
        "fetch_shipping_cost": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Fetch courier info and cost for checkout.",
            "label": "Fetch courier cost",
        },
        "fetch_waybill": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Fetch waybill info.",
            "label": "Fetch waybill",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}

        self.config = PluginConfig(
            fetch_shipping_cost=configuration["fetch_shipping_cost"],
            fetch_waybill=configuration["fetch_waybill"],
            params={
                "key": configuration["api_key"],
                "courier": ":".join(json.loads(configuration["courier"])),
                "originType": DESTINATION_TYPE,
                "destinationType": DESTINATION_TYPE,
            },
        )

    def fetch_shipping_costs(
        self, address: "Address", weight: int, previous_value: list
    ) -> List["Courier"]:
        if previous_value:
            return previous_value

        site_settings = SiteSettings.objects.select_related("company_address").first()
        if (
            self.config.fetch_shipping_cost
            and self.config.params["courier"]
            and site_settings.company_address
        ):
            origin = site_settings.company_address.sub_district_id
            destination = address.sub_district_id
            data = self.config.params.copy()
            key = data.pop("key")
            data["origin"] = origin
            data["destination"] = destination
            data["weight"] = weight
            headers = {"key": key}
            r = requests.post(URL_COST, headers=headers, data=data)
            if r.status_code == 200:
                try:
                    results = r.json()["rajaongkir"]["results"]
                    data = [
                        Courier(
                            code=result["code"],
                            name=result["name"],
                            services=[
                                CourierService(
                                    cost=service["cost"][0].get("value", 0),
                                    service=service.get("service", ""),
                                    description=service.get("description", ""),
                                    etd=service["cost"][0].get("etd", ""),
                                )
                                for service in result["costs"]
                            ],
                        )
                        for result in results
                        if result["costs"]
                    ]
                    return data
                except Exception:
                    return previous_value
        return previous_value

    def fetch_waybill(
        self, waybill: str, courier: str, previous_value: "Waybill"
    ) -> Optional["Waybill"]:
        if self.config.fetch_waybill:
            headers = {"key": self.config.params["key"]}
            data = {"courier": courier.lower(), "waybill": waybill}
            r = requests.post(URL_WAYBILL, headers=headers, data=data)
            if r.status_code == 200:
                try:
                    result = r.json()["rajaongkir"]["result"]
                    status = result["delivery_status"]
                    histories = result["manifest"]
                    status = WaybillStatus(
                        status=status["status"],
                        receiver=status["pod_receiver"],
                        date=f"{status['pod_date']} {status['pod_time']}",
                    )
                    histories = [
                        WaybillHistory(
                            date=f"{history['manifest_date']} {history['manifest_time']}",
                            description=history["manifest_description"],
                            city=history["city_name"],
                        )
                        for history in histories
                    ]
                    return Waybill(status=status, histories=histories)
                except Exception:
                    return previous_value
        return previous_value
