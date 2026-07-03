import re

import httpx

from .base import BaseChecker, Offer

INDEX_URL = "https://u1host.com/ru"
BASE_URL = "https://u1host.com"
ORDER_URL_TEMPLATE = (
    "https://my.u1host.com?func=register&redirect=startpage%3Dvds%26startform%3Dvds"
    "%252Eorder%252Eparam%26pricelist%3D{tariff_id}%26period%3D1%26project%3D3"
)

MAIN_JS_SRC_RE = re.compile(r'src="(/main\.js\?v=[^"]+)"')
SOLD_OUT_RE = re.compile(r"const\s+isSoldOut\s*=\s*(true|false)\s*;")
TARIFFS_BLOCK_RE = re.compile(r"const\s+tariffs\s*=\s*\{(.*?)\n\s*\};", re.DOTALL)
GROUP_RE = re.compile(r"'([\w-]+)':\s*\[(.*?)\]\s*,?\s*(?=\n\s*'[\w-]+':|\Z)", re.DOTALL)
ITEM_RE = re.compile(r"\{\s*name:.*?id:\s*\d+\s*\}", re.DOTALL)

COUNTRY_NAMES = {
    "de": "Германия",
    "nl": "Нидерланды",
    "fi": "Финляндия",
}
CPU_NAMES = {
    "7950x3d": "AMD Ryzen 9 7950X3D",
    "5950x": "AMD Ryzen 9 5950X",
}


def _extract_field(text: str, field: str) -> str | None:
    m = re.search(rf"{field}\s*:\s*'([^']*)'", text)
    if m:
        return m.group(1)
    m = re.search(rf"{field}\s*:\s*`?(\d+)", text)
    return m.group(1) if m else None


class U1HostChecker(BaseChecker):
    name = "u1host"
    display_name = "u1host.com"
    price_limit = 1000

    async def fetch_available(self) -> list[Offer]:
        async with httpx.AsyncClient(timeout=15, headers={"User-Agent": "Mozilla/5.0"}) as client:
            index_resp = await client.get(INDEX_URL)
            index_resp.raise_for_status()
            src_match = MAIN_JS_SRC_RE.search(index_resp.text)
            if not src_match:
                raise RuntimeError("main.js reference not found on u1host.com index page")

            js_resp = await client.get(BASE_URL + src_match.group(1))
            js_resp.raise_for_status()
            js = js_resp.text

        sold_out_match = SOLD_OUT_RE.search(js)
        if not sold_out_match or sold_out_match.group(1) == "true":
            return []

        tariffs_match = TARIFFS_BLOCK_RE.search(js)
        if not tariffs_match:
            raise RuntimeError("tariffs block not found in main.js")

        offers: list[Offer] = []
        for group_name, group_body in GROUP_RE.findall(tariffs_match.group(1)):
            if "3900" in group_name:
                continue  # промо-тариф, не интересует

            country_code, _, cpu_code = group_name.partition("-r9-")
            country = COUNTRY_NAMES.get(country_code, country_code)
            cpu_name = CPU_NAMES.get(cpu_code, cpu_code)

            for item_text in ITEM_RE.findall(group_body):
                price_match = re.search(r"price:\s*formatPrice\((\d+)\)", item_text)
                id_match = re.search(r"id:\s*(\d+)", item_text)
                if not price_match or not id_match:
                    continue
                price = int(price_match.group(1))
                if price >= self.price_limit:
                    continue

                tariff_id = int(id_match.group(1))
                ram = _extract_field(item_text, "ram")
                disk = _extract_field(item_text, "disk")
                network = _extract_field(item_text, "network")

                offers.append(
                    Offer(
                        checker_name=self.name,
                        key=f"{country_code}:{tariff_id}",
                        country=country,
                        category=f"Облачный VPS ({cpu_name})",
                        name=_extract_field(item_text, "name") or group_name,
                        cpu=_extract_field(item_text, "cpu") or "",
                        ram=f"{ram} GB" if ram else "",
                        disk=f"{disk} GB" if disk else "",
                        network=f"{network} Gbps" if network else "",
                        price=price,
                        currency="₽",
                        order_url=ORDER_URL_TEMPLATE.format(tariff_id=tariff_id),
                    )
                )

        return offers
