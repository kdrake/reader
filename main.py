import argparse

import requests

from lib.config import get_config
from lib.reader import Reader
from lib.utils import save_by_url


def main():
    parser = argparse.ArgumentParser(description='Collect useful information from given url.')
    parser.add_argument('url', help='Url of a web page.')
    args = parser.parse_args()

    # load content by given url
    r = requests.get(args.url)
    r.raise_for_status()

    # extract useful data
    config = get_config()

    reader = Reader(config)
    pretty_content = reader.from_string(r.text)

    # save retrieved info
    file_dst = save_by_url(args.url, pretty_content)
    print('Useful content save to: "{}".'.format(file_dst))


if __name__ == '__main__':
    main()
