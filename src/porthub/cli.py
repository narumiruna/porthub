import logging

import typer

logger = logging.getLogger(__name__)


app = typer.Typer()


@app.command()
def main() -> None:
    format_str = "%(asctime)s | %(levelname)s | %(name)s:%(lineno)d - %(message)s"
    logging.basicConfig(format=format_str, level=logging.INFO)
    logger.info("Hello, world!")


@app.command()
def search(query: str) -> list[str]:
    logger.info("Searching for: %s", query)
    # Placeholder for actual search logic
    return ["result1", "result2", "result3"]


@app.command()
def get(key: str) -> str:
    logger.info("Getting value for key: %s", key)
    # Placeholder for actual get logic
    return "value"


@app.command()
def set(key: str, value: str) -> None:
    logger.info("Setting value for key: %s to %s", key, value)
    # Placeholder for actual set logic
