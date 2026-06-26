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

@dataclass(frozen=True, slots=True)
class DownloadSummary:
    """Итоговые результаты серии загрузок."""

    request_count: int
    total_elapsed_seconds: float
    total_downloaded_bytes: int

    @property
    def average_request_time(self) -> float:
        """Среднее время выполнения одного запроса."""
        return self.total_elapsed_seconds / self.request_count

    @property
    def total_downloaded_megabytes(self) -> float:
        """Общий объём загруженных данных в мегабайтах."""
        return self.total_downloaded_bytes / 1_000_000

    @property
    def average_speed_megabytes_per_second(self) -> float:
        """Средняя скорость загрузки в мегабайтах в секунду."""
        if self.total_elapsed_seconds == 0:
            return 0.0

        return self.total_downloaded_megabytes / self.total_elapsed_seconds


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
        logger.error("Не удалось выполнить загрузку %s: %s", url, exc)

    # Вычисляем длительность запроса
    elapsed_seconds = perf_counter() - started_at

    return DownloadResult(
        elapsed_seconds=elapsed_seconds,
        downloaded_bytes=downloaded_bytes,
    )


def measure_download_speed(
    url: str,
    request_count: int = DEFAULT_REQUEST_COUNT,
    timeout: int = DEFAULT_TIMEOUT,
) -> DownloadSummary:
    """Последовательно загружает изображение несколько раз.

    Args:
        url(str): URL загружаемого изображения.
        request_count(int): Количество последовательных загрузок.
        timeout(int): Тайм-аут каждого HTTP-запроса в секундах.

    Returns:
        Итоговые результаты серии загрузок.
    """
    if request_count <= 0:
        raise ValueError("Количество запросов должно быть больше нуля")

    if timeout <= 0:
        raise ValueError("Тайм-аут должен быть больше нуля")

    # Общие счетчики затраченного времени и загруженных байт
    total_elapsed_seconds = 0.0
    total_downloaded_bytes = 0

    # Создаем общую сессию для всех запросов
    with requests.Session() as session:
        for request_number in range(1, request_count + 1):
            result = download_image(
                session=session,
                url=url,
                timeout=timeout,
            )

            total_elapsed_seconds += result.elapsed_seconds
            total_downloaded_bytes += result.downloaded_bytes

            logger.info(
                "Загрузка %d/%d завершена: %.3f сек., %d байт",
                request_number,
                request_count,
                result.elapsed_seconds,
                result.downloaded_bytes,
            )

    return DownloadSummary(
        request_count=request_count,
        total_elapsed_seconds=total_elapsed_seconds,
        total_downloaded_bytes=total_downloaded_bytes,
    )

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    summary = measure_download_speed(
        "https://raw.githubusercontent.com/github/explore/main/topics/python/python.png"
    )

    print("\nИтоги:")
    print(f"Среднее время запроса: {summary.average_request_time:.3f} сек.")
    print(f"Объём скачанных данных: {summary.total_downloaded_megabytes:.3f} МБ")
    print(f"Средняя скорость: {summary.average_speed_megabytes_per_second:.3f} МБ/с")




