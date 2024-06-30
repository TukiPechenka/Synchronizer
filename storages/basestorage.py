from abc import abstractmethod
from requests import session


class BaseStorage:

    def __init__(self, token: str, watched_directory_path: str):
        self.token = token
        self.directory_path = watched_directory_path

    @abstractmethod
    def load(self, path: str): ...

    @abstractmethod
    def reload(self, path: str): ...

    @abstractmethod
    def delete(self, filename: str): ...

    @abstractmethod
    def get_info(self): ...
