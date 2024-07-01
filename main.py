from config import config
import logging
from storages.yandexstorage import YandexStorage


logger = logging.getLogger("synchronizer")
logging.basicConfig(level="INFO")
handler = logging.FileHandler(filename=config["log_file"], encoding="UTF-8")
formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


if __name__ == "__main__":
    storage = YandexStorage(
        token=config["token"],
        watched_directory_path=config["directory_path"],
        directory_name=config["directory_name"],
        period_time=int(config["period_time"]),
        logger=logger,
        ignore_files=config["ignore_files"].split(", "),
    )
    storage.start_work()
