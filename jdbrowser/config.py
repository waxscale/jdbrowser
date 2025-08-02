import os
import configparser

def read_config():
    config = configparser.ConfigParser()
    cfg_path = os.path.expanduser('~/.config/jdbrowser/config.conf')
    config.read(cfg_path)
    return config.get('settings', 'repository', fallback=os.getcwd())