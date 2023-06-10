import asyncio
import logging
import time
import argparse
import pprint
import aiohttp
from datetime import date, timedelta

logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)

# Список доступных валют
CURRENCIES = ["USD", "EUR", "CHF", "GBP", "PLZ", "SEK", "XAU", "CAD"]


def data_parser(response_data: dict, currencies):
    results = []
    if "exchangeRate" in response_data:
        daily_data = {}
        for i in response_data["exchangeRate"]:
            if i["currency"] in currencies:
                daily_data[i["currency"]] = {
                    "sale": i.get("saleRateNB"),
                    "purchase": i.get("purchaseRateNB"),
                }
        results.append({response_data["date"]: daily_data})
    return results


def today_str(days: int = None) -> str:
    if 0 > days or days > 10:
        raise ValueError(f"Number of days should be between 1 and 10. Got {days} days")

    result = []
    today_date = date.today()
    month = today_date.month
    year = today_date.year
    day = today_date.day
    result.append(f"{day:02d}.{month:02d}.{year}")

    if days is not None:
        for i in range(1, days):
            prev_date = today_date - timedelta(days=i)
            prev_month = prev_date.month
            prev_year = prev_date.year
            prev_day = prev_date.day
            result.append(f"{prev_day:02d}.{prev_month:02d}.{prev_year}")
    return result


class API:
    def __init__(self, session):
        self.session = session

    async def get(self, url):
        async with self.session.get(url, ssl=False) as response:
            return await response.json()


async def result_to_api(days=list, currencies=["USD", "EUR"]):
    results = []
    async with aiohttp.ClientSession() as session:
        api = API(session)
        for day in days:
            url = f"https://api.privatbank.ua/p24api/exchange_rates?date={day}"
            start_time = time.time()
            try:
                response_data = await api.get(url)
            except aiohttp.ClientError as e:
                logging.error(f"Request failed: {e}")
                continue
            else:
                elapsed_time = time.time() - start_time
                logging.info(
                    f"Response received for {day}. Time elapsed: {elapsed_time} seconds"
                )
                result = data_parser(response_data, currencies)
                results.extend(result)

    return results


async def main(days, currencies) -> dict:
    today_date = today_str(days)
    result = await result_to_api(today_date, currencies)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("days", type=int, default=None)
    parser.add_argument(
        "-c",
        "--currencies",
        nargs="+",
        default=["USD", "EUR"],
        help="Currencies to get rates for. Available options: " + ", ".join(CURRENCIES),
    )
    args = parser.parse_args()
    pp = pprint.PrettyPrinter(indent=2)
    results = asyncio.run(main(args.days, args.currencies))
    pp.pprint(results)
