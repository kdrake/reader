import os

from yaml import load

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


def get_config():
    config_file_path = os.path.join(os.path.dirname(__file__), os.pardir, 'config.yml')
    with open(config_file_path, 'r') as f:
        config = load(f, Loader=Loader)
    return config
