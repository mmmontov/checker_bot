import httpx

from .base import BaseChecker, Offer

INDEX_URL = "https://hostoff.net/ru/vps"

COUNTRY_NAMES = {
    "PL": "Польша",
    "NL": "Нидерланды",
}


def _monthly_price(location: dict) -> dict | None:
    for price in location["prices"]:
        if price["billing_period_code"] == "monthly":
            return price
    return None


def _format_network(bandwidth_mbps: int) -> str:
    if bandwidth_mbps >= 1000:
        gbps = bandwidth_mbps / 1000
        return f"{gbps:g} Gbps"
    return f"{bandwidth_mbps} Mbps"


class HostoffChecker(BaseChecker):
    name = "hostoff"
    display_name = "hostoff.net"

    async def fetch_available(self) -> list[Offer]:
        async with httpx.AsyncClient(timeout=15, headers={"User-Agent": "Mozilla/5.0"}) as client:
            resp = await client.get(
                INDEX_URL,
                headers={"X-Inertia": "true", "Accept": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()

        try:
            plans = data["props"]["vpsData"]["data"]["service_plans"]
        except KeyError as exc:
            raise RuntimeError("service_plans not found in hostoff.net response") from exc

        cheapest_by_country: dict[str, tuple[dict, dict, dict]] = {}
        for plan in plans:
            for location in plan["locations"]:
                country_code = location["country_code"]
                if country_code not in COUNTRY_NAMES:
                    continue

                price = _monthly_price(location)
                if price is None:
                    continue

                current = cheapest_by_country.get(country_code)
                if current is None or price["price"] < current[2]["price"]:
                    cheapest_by_country[country_code] = (plan, location, price)

        if not cheapest_by_country:
            raise RuntimeError("no PL/NL locations found in hostoff.net response")

        offers: list[Offer] = []
        for country_code, (plan, location, price) in cheapest_by_country.items():
            if not location["is_available"]:
                continue

            specs = plan["specs"]
            offers.append(
                Offer(
                    checker_name=self.name,
                    key=f"{country_code}:{plan['id']}:{location['location_id']}",
                    country=COUNTRY_NAMES[country_code],
                    category=f"VPS ({plan['description']})",
                    name=plan["name"],
                    cpu=f"{specs['cpu_cores']} vCPU",
                    ram=f"{specs['ram_mb'] // 1024} GB",
                    disk=f"{specs['storage_gb']} GB",
                    network=_format_network(specs["bandwidth_speed"]),
                    price=round(price["price"] / 1e8, 2),
                    currency="€",
                    order_url=INDEX_URL,
                )
            )

        return offers
