import os

import pytest

from lib.utils import get_filepath_by_url

examples = [
    ('http://e1.ru', 'index.txt', os.path.join('e1.ru')),
    ('http://e1.ru?', 'index.txt', os.path.join('e1.ru')),
    ('http://e1.ru?a=1&a=2&b=3', 'index.txt', os.path.join('e1.ru', 'a=1', 'a=2', 'b=3')),
    ('http://www.filmz.ru/pub/2/29858_1.htm', '29858_1.txt', os.path.join('www.filmz.ru', 'pub', '2')),
    ('http://www.filmz.ru/pub//29858_1.htm', '29858_1.txt', os.path.join('www.filmz.ru', 'pub')),
    ('http://www.filmz.ru/pub/2/29858_1.htm?', '29858_1.txt', os.path.join('www.filmz.ru', 'pub', '2')),
    ('http://www.filmz.ru/pub/2/29858_1.htm?a=1', '29858_1.txt', os.path.join('www.filmz.ru', 'pub', '2')),
    ('http://lenta.ru/articles/2015/08/11/salarystop/', 'salarystop.txt',
     os.path.join('lenta.ru', 'articles', '2015', '08', '11')),
]


@pytest.mark.parametrize("case", examples)
def test_should_pass(case):
    url, result_filename, result_file_path = case

    file_path, filename = get_filepath_by_url(url)

    assert filename == result_filename
    assert file_path == result_file_path
