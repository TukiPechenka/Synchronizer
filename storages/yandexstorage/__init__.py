import logging

import requests

from ..basestorage import BaseStorage
from time import sleep
import os


class YandexStorage(BaseStorage):
    __url = "https://cloud-api.yandex.net/v1/disk/resources"

    def __init__(
        self,
        directory_name: str,
        period_time: int = 1,
        logger: logging.Logger = None,
        ignore_files: list = None,
        **kwargs,
    ):
        self.__headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f'OAuth {kwargs["token"]}',
        }

        self.__directory = directory_name
        if period_time <= 0:
            raise ValueError(
                "Время между синхронизациями папки должно быть "
                f"больше 0, а задано {period_time}"
            )
        self.__period_time = period_time
        self.__session = requests.session()
        self.logger = logger or logging.getLogger("YandexStorage")

        super().__init__(**kwargs)
        try:
            self.get_or_create_dir()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                "Прежде чем запускать программу, убедитесь, "
                "что установлено интернет соединение."
            )

        if not os.path.isdir(
            kwargs["watched_directory_path"].encode("UTF-16").decode("UTF-16")
        ):
            raise ValueError(
                f"""Указанный путь к директории отсутствует или
                указан путь к файлу.
                    Путь: {kwargs["watched_directory_path"]}"""
            )

        self.ignore_files = ignore_files or []

        self.logger.info("Программа синхронизации файлов "
                         f"с директорией {self.directory_path} началась")

    def get_or_create_dir(self):
        response = self.__session.get(
            self.__url + f"?path={self.__directory}", headers=self.__headers
        )
        if response.status_code == 401:
            raise ValueError(f"Некорректный токен: {self.token}")

        if response.json().get("type") == "dir":
            return
        self.__session.put(
            self.__url + f"?path={self.__directory}", headers=self.__headers
        )

    def load(self, filename: str):
        response = self.__session.get(
            self.__url + f"/upload?path={self.__directory}/{filename}&"
                         "overwrite=false",
            headers=self.__headers,
        ).json()
        with open(self.directory_path + f"/{filename}") as file:
            data = file.read()
        self.__session.put(response["href"], data=data)
        self.logger.info(f"Файл {filename} успешно записан.")

    def reload(self, filename: str):
        response = self.__session.get(
            self.__url + f"/upload?path={self.__directory}/{filename}&"
                         "overwrite=true",
            headers=self.__headers,
        ).json()
        with open(self.directory_path + f"/{filename}") as file:
            data = file.read()
        self.__session.put(response["href"], data=data)
        self.logger.info(f"Файл {filename} успешно перезаписан.")

    def delete(self, filename: str):
        self.__session.delete(
            self.__url + f"?path={self.__directory}/{filename}",
            headers=self.__headers
        )
        self.logger.info(f"Файл {filename} успешно удалён.")

    def get_info(self) -> dict:
        response = self.__session.get(
            self.__url + f"?path={self.__directory}", headers=self.__headers
        ).json()
        files_list = response["_embedded"]["items"]
        files = dict()
        for index, file in enumerate(files_list):
            files[file["name"]] = self.__session.get(
                file["file"]
            ).content.decode()
        return files

    def work(self):
        self.logger.info(f"Цикл проверки директории")
        try:
            files = self.get_info()
            for file in os.listdir(self.directory_path):
                if file in self.ignore_files or os.path.isdir(
                    self.directory_path + f"/{file}"
                ):
                    continue
                try:
                    with (open(self.directory_path + "/" + file, "r")
                          as open_file):
                        read_file = open_file.read()
                        if read_file == files.get(file):
                            self.logger.info(
                                f"Файл {file} остался без изменений"
                            )
                            files.pop(file)
                        elif (
                                files.get(file) is not None and
                                read_file != files.get(file)
                        ):
                            self.reload(file)
                            files.pop(file)
                        else:
                            self.load(file)
                except PermissionError:
                    self.logger.error(f"Отказ в доступе к файлу {file}")
                except requests.exceptions.ConnectionError:
                    self.logger.error("Ошибка соединения при "
                                      f"работе с файлом {file}")
            for file in files:
                try:
                    self.delete(file)
                except requests.exceptions.ConnectionError:
                    self.logger.error(
                        "Ошибка соединения при удалении "
                        f"файла {file} из облака"
                    )
        except requests.exceptions.ConnectionError:
            self.logger.error(
                "Ошибка соединения при получении данных о файлах из облака."
            )

    def start_work(self):
        self.logger.info(
            "Программа синхронизации файлов начинает "
            f"работу с директорией {self.directory_path}"
        )
        while True:
            self.work()
            sleep(self.__period_time)
