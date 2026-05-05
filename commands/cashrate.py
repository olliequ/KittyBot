import asyncio
import random
import re
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Iterable

import aiohttp
from bs4 import BeautifulSoup
from bs4.element import Tag
import lightbulb

plugin = lightbulb.Plugin("CashRate")

CASH_RATE_URL = "https://www.rba.gov.au/statistics/cash-rate/"
# Cash rate values are small percentages; this filters out years or other large numbers.
MAX_REASONABLE_RATE = 50.0

LOADING_MESSAGES = [
    "Kitti is pawing through the RBA scrolls... 🐾",
    "Kitti is chasing the cash rate laser pointer... 💡",
    "Kitti is listening to the Reserve Bank's purr-ess release... 📰",
]

FUTURE_DATE_MESSAGES = [
    "Nice try, time traveler. Kitti only lives in the meow. 🐱",
    "That date is in the future — even Kitti's whiskers can't see it yet!",
    "Meow no, that day hasn't happened yet. Try a past date.",
    "Kitti refuses to predict the future. She's busy napping.",
]

USER_DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%d %b %Y",
    "%d %B %Y",
)

TABLE_DATE_FORMATS = (
    "%d %B %Y",
    "%d %b %Y",
    "%Y-%m-%d",
)


@dataclass(frozen=True)
class CashRateEntry:
    date: date
    rate: str


def _parse_rate(value: str) -> str | None:
    match = re.search(r"\b(\d+(?:\.\d+)?)\s*%?", value)
    if not match:
        return None
    rate = float(match.group(1))
    if rate > MAX_REASONABLE_RATE:
        return None
    return f"{match.group(1)}%"


def _parse_table_date(value: str) -> date | None:
    cleaned = " ".join(value.split())
    for fmt in TABLE_DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def _parse_user_date(value: str) -> date | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    try:
        return datetime.fromisoformat(cleaned).date()
    except ValueError:
        pass
    for fmt in USER_DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def _tag_list(elements: Iterable[object]) -> list[Tag]:
    return [element for element in elements if isinstance(element, Tag)]


def _parse_table(table: Tag) -> list[CashRateEntry]:
    entries: list[CashRateEntry] = []
    for row in _tag_list(table.find_all("tr")):
        cells = _tag_list(row.find_all(["th", "td"]))
        if len(cells) < 2:
            continue
        texts = [cell.get_text(" ", strip=True) for cell in cells]
        row_date = None
        row_rate = None
        for text in texts:
            if row_date is None:
                row_date = _parse_table_date(text)
            if row_rate is None:
                row_rate = _parse_rate(text)
            if row_date and row_rate:
                break
        if row_date and row_rate:
            entries.append(CashRateEntry(row_date, row_rate))
    return entries


def _find_cash_rate_entries(soup: BeautifulSoup) -> list[CashRateEntry]:
    candidates: list[list[CashRateEntry]] = []
    for table in _tag_list(soup.find_all("table")):
        entries = _parse_table(table)
        if not entries:
            continue
        header_cells = _tag_list(table.find_all("th"))
        header_text = " ".join(
            cell.get_text(" ", strip=True).lower() for cell in header_cells
        )
        if "cash rate" in header_text or "target" in header_text:
            return entries
        candidates.append(entries)
    if candidates:
        return max(candidates, key=len)
    return []


def _normalize_entries(entries: Iterable[CashRateEntry]) -> list[CashRateEntry]:
    unique: dict[date, CashRateEntry] = {}
    for entry in entries:
        unique.setdefault(entry.date, entry)
    return sorted(unique.values(), key=lambda entry: entry.date)


def _format_relative_period(start: date, end: date) -> str:
    parts: list[str] = []
    years = end.year - start.year
    months = end.month - start.month
    days = end.day - start.day
    if days < 0:
        prev_month = 12 if end.month == 1 else end.month - 1
        prev_year = end.year - 1 if end.month == 1 else end.year
        days += monthrange(prev_year, prev_month)[1]
        months -= 1
    if months < 0:
        months += 12
        years -= 1
    if years:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if months:
        parts.append(f"{months} month{'s' if months != 1 else ''}")
    if days or not parts:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    return " ".join(parts)


def _count_changes_since(entries: list[CashRateEntry], since: date) -> int:
    return sum(1 for entry in entries if entry.date >= since)


def _find_rate_for_date(
    entries: list[CashRateEntry], target_date: date
) -> CashRateEntry | None:
    result = None
    for entry in entries:
        if entry.date <= target_date:
            result = entry
        else:
            break
    return result


def _format_latest(entry: CashRateEntry) -> str:
    return f"Latest RBA cash rate: {entry.rate} (as of {entry.date:%Y-%m-%d})."


def _format_history(
    entry: CashRateEntry, target_date: date, today: date, changes_since: int
) -> str:
    days_ago = (today - target_date).days
    day_label = "day" if days_ago == 1 else "days"
    period = _format_relative_period(target_date, today)
    target_label = target_date.strftime("%Y-%m-%d")
    entry_label = entry.date.strftime("%Y-%m-%d")
    if entry.date == target_date:
        rate_line = f"Cash rate on {target_label}: {entry.rate}."
    else:
        rate_line = (
            f"Cash rate on {target_label}: {entry.rate} (effective {entry_label})."
        )
    changes_line = f"Changes since then: {changes_since}."
    age_line = f"That day was {days_ago} {day_label} ({period}) ago from now."
    return "\n".join([rate_line, changes_line, age_line])


@plugin.command
@lightbulb.add_cooldown(10, 1, lightbulb.UserBucket)
@lightbulb.option(
    "date",
    "Date to look up (YYYY-MM-DD). Leave blank for the latest cash rate.",
    required=False,
)
@lightbulb.command("cashrate", "Get the current RBA cash rate.")
@lightbulb.implements(lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    await ctx.respond(random.choice(LOADING_MESSAGES))
    bot = plugin.bot
    session = getattr(bot.d, "aio_session", None)
    if not isinstance(session, aiohttp.ClientSession) or session.closed:
        await ctx.edit_last_response(
            "Kitti can't reach the RBA right meow. Try again later."
        )
        return

    try:
        async with session.get(
            CASH_RATE_URL, timeout=aiohttp.ClientTimeout(total=15)
        ) as response:
            if response.status != 200:
                await ctx.edit_last_response(
                    f"Kitti couldn't fetch the cash rate (HTTP {response.status})."
                )
                return
            html = await response.text()
    except (aiohttp.ClientError, asyncio.TimeoutError):
        await ctx.edit_last_response(
            "Kitti couldn't reach the RBA cash rate page right meow."
        )
        return

    entries = _normalize_entries(
        _find_cash_rate_entries(BeautifulSoup(html, "html.parser"))
    )
    if not entries:
        await ctx.edit_last_response(
            "Kitti couldn't find the cash rate table on the RBA page."
        )
        return

    today = datetime.now(timezone.utc).date()
    latest_entry = entries[-1]
    user_date = ctx.options.date
    if not user_date:
        await ctx.edit_last_response(_format_latest(latest_entry))
        return

    parsed_date = _parse_user_date(str(user_date))
    if parsed_date is None:
        await ctx.edit_last_response(
            "Kitti couldn't read that date. Try YYYY-MM-DD (e.g. 2024-05-07)."
        )
        return

    if parsed_date > today:
        await ctx.edit_last_response(random.choice(FUTURE_DATE_MESSAGES))
        return

    entry = _find_rate_for_date(entries, parsed_date)
    if entry is None:
        earliest = entries[0]
        await ctx.edit_last_response(
            "Kitti's memory only goes back to "
            f"{earliest.date:%Y-%m-%d} (rate {earliest.rate})."
        )
        return

    changes_since = _count_changes_since(entries, parsed_date)
    await ctx.edit_last_response(
        _format_history(entry, parsed_date, today, changes_since)
    )


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
