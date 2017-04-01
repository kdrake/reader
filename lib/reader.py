from .formatter import Formatter
from .parser import Parser


class Reader:
    def __init__(self, cfg):
        self.cfg = cfg
        self.parser = Parser(self.cfg)
        self.formatter = Formatter(self.cfg.get('max_line_length'))

    def from_string(self, text):
        parse_result = self.parser.get_article(text)
        return self.formatter.to_string(parse_result)
