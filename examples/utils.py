import logging
import logging.config
import logging.handlers
from pathlib import Path

import yaml


def init_logging():
    config_as_str = Path(__file__).parent.joinpath("./logger.yml").read_text()
    config = yaml.safe_load(config_as_str)
    logging.config.dictConfig(config)
