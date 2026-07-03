from checkers import Offer


def _format_offer(offer: Offer) -> str:
    return (
        f"<b>{offer.name}</b> ({offer.country})\n"
        f"{offer.category}\n"
        f"CPU: {offer.cpu} | RAM: {offer.ram} | Диск: {offer.disk} | Сеть: {offer.network}\n"
        f"Цена: <b>{offer.price} {offer.currency}/мес</b>\n"
        f'<a href="{offer.order_url}">Заказать</a>'
    )


def format_new_offers(checker_name: str, offers: list[Offer]) -> str:
    header = f"🟢 На {checker_name} появились новые серверы в наличии!"
    body = "\n\n".join(_format_offer(o) for o in offers)
    return f"{header}\n\n{body}"


def format_status(checker_name: str, offers: list[Offer]) -> str:
    if not offers:
        return f"{checker_name}: сейчас подходящих серверов в наличии нет."
    header = f"{checker_name}: сейчас в наличии {len(offers)} предложений:"
    body = "\n\n".join(_format_offer(o) for o in offers)
    return f"{header}\n\n{body}"
