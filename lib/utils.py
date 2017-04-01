import os
from urllib.parse import urlparse


def save_by_url(url, content):
    path, filename = get_filepath_by_url(url)

    dst_path = os.path.join(os.getcwd(), 'result', path)
    if not os.path.isdir(dst_path):
        os.makedirs(dst_path)

    dst = os.path.join(dst_path, filename)
    with open(dst, 'w', encoding='utf-8') as f:
        f.write(content)

    return dst


def get_filepath_by_url(url):
    parse_result = urlparse(url)

    path_list = [dir_name for dir_name in parse_result.path.split('/') if dir_name.strip()]
    if path_list:
        path = os.path.join(parse_result.netloc, *path_list[:-1])
        filename = '{}.txt'.format(path_list[-1].split('.')[0])
    else:
        qs_list = [dir_name for dir_name in parse_result.query.split('&') if dir_name.strip()]
        path = os.path.join(parse_result.netloc, *qs_list)
        filename = 'index.txt'

    return path, filename
