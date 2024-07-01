from configparser import ConfigParser


config = ConfigParser()
config.read("config.ini")
config = dict(config["SETTINGS"])
