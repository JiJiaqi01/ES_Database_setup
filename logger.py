from logging import getLogger, FileHandler, Formatter, DEBUG

from datetime import datetime

logger = getLogger()

logger.setLevel(DEBUG)

handler = FileHandler(f".app.log")

timestamp_format = "%Y-%m-%d %H:%M:%S"

formatter = Formatter(
    "%(asctime)s.%(msecs)03d  %(name)s - %(levelname)s - %(message)s",
    datefmt=timestamp_format,
)

handler.setFormatter(formatter)

logger.addHandler(handler)

logger.debug("logger initialized")
