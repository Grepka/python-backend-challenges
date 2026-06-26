import logging
from dataclasses import dataclass
from time import perf_counter

import requests
from requests import RequestException


logger = logging.getLogger(__name__)

DEFAULT_REQUEST_COUNT = 10  # Количество загрузок из задания
DEFAULT_TIMEOUT = 30        # Ограничение времени запросов
CHUNK_SIZE = 64 * 1024      # Количество байтов, считываемых за одну итерацию

@dataclass(frozen=True, slots=True)
class DownloadResult:
    """Результат одной загрузки изображения."""
    elapsed_seconds: float
    downloaded_bytes: int


def download_image(session: requests.Session, url: str, timeout: int) -> DownloadResult:
    """Единоразовая загрузка изображения.

    Args:
        session(requests.Session): HTTP-сессия для переиспользования соединения.
        url(str): URL загружаемого изображения.
        timeout(int): Максимальное время ожидания ответа в секундах.

    Returns:
        Результат загрузки, содержащий длительность и количество загруженных байт.
    """

    started_at = perf_counter()
    downloaded_bytes = 0

    try:
        with session.get(url, stream=True, timeout=timeout) as response:
            response.raise_for_status()

            # Читаем ответ частями, чтобы не загружать весь файл в память.
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    downloaded_bytes += len(chunk)
    except RequestException as exc:
        logger.error("Не удалось выполнить загрузку %s: %s",url, exc)
        raise

    # Вычисляем длительность запроса
    elapsed_seconds = perf_counter() - started_at

    return DownloadResult(
        elapsed_seconds=elapsed_seconds,
        downloaded_bytes=downloaded_bytes,
    )




