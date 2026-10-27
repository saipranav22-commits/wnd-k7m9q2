import asyncio
import logging
from typing import List, Dict, Any, Optional
import httpx
from backend.config import (
    ELEXON_FUELHH_URL,
    ELEXON_WINDFOR_URL,
    REQUEST_TIMEOUT_SECONDS,
    MAX_RETRIES,
    INITIAL_BACKOFF_SECONDS,
)

logger = logging.getLogger(__name__)

class ElexonClient:
    def __init__(self, timeout: float = REQUEST_TIMEOUT_SECONDS):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "AERIS-WindForecastIntelligence/1.0",
            "Accept": "application/json",
        }

    async def _get_with_retry(self, url: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        backoff = INITIAL_BACKOFF_SECONDS
        last_exception = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, params=params, headers=self.headers)

                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list):
                            return data
                        elif isinstance(data, dict) and "data" in data:
                            return data["data"]
                        return []

                    if response.status_code == 429:
                        retry_after = float(response.headers.get("Retry-After", backoff * 2))
                        logger.warning(f"Rate limited (429) by Elexon. Retrying in {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        continue

                    if response.status_code >= 500:
                        logger.warning(f"Server error {response.status_code} from Elexon. Attempt {attempt}/{MAX_RETRIES}")
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue

                    # If client error (400, 404, etc.)
                    response.raise_for_status()

            except (httpx.RequestError, httpx.TimeoutException) as exc:
                last_exception = exc
                logger.warning(f"Network error on attempt {attempt}/{MAX_RETRIES} to {url}: {exc}")
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(backoff)
                    backoff *= 2

        logger.error(f"Failed to fetch from {url} after {MAX_RETRIES} attempts. Error: {last_exception}")
        if last_exception:
            raise last_exception
        return []

    async def fetch_fuelhh_actuals(
        self,
        settlement_date_from: str,
        settlement_date_to: str,
        fuel_type: str = "WIND"
    ) -> List[Dict[str, Any]]:
        """
        Fetch outturn actuals from FUELHH stream endpoint.
        Format of dates: YYYY-MM-DD
        """
        params = {
            "settlementDateFrom": settlement_date_from,
            "settlementDateTo": settlement_date_to,
            "fuelType": fuel_type,
        }
        logger.info(f"Fetching FUELHH wind actuals from {settlement_date_from} to {settlement_date_to}")
        records = await self._get_with_retry(ELEXON_FUELHH_URL, params=params)
        # Extra client-side filter to strictly guarantee only WIND
        return [r for r in records if r.get("fuelType") == fuel_type]

    async def fetch_windfor_forecasts(
        self,
        publish_datetime_from: str,
        publish_datetime_to: str
    ) -> List[Dict[str, Any]]:
        """
        Fetch forecast history from WINDFOR stream endpoint.
        Format of datetimes: ISO 8601 UTC (e.g. 2026-01-01T00:00:00Z)
        """
        params = {
            "publishDateTimeFrom": publish_datetime_from,
            "publishDateTimeTo": publish_datetime_to,
        }
        logger.info(f"Fetching WINDFOR forecasts published from {publish_datetime_from} to {publish_datetime_to}")
        return await self._get_with_retry(ELEXON_WINDFOR_URL, params=params)
