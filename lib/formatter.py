import os
import textwrap

from bs4 import NavigableString
from bs4.element import PreformattedString


class Formatter:
    def __init__(self, width):
        self.width = width
        self.tags_to_string = ['b', 'strong', 'i', 'span']

    def to_string(self, parse_result):
        result = self._format_title(parse_result.title)
        result += os.linesep
        result += self._format_body(parse_result.content)
        return result

    def _format_title(self, soup):
        format_link(soup)
        tag_to_string(soup, self.tags_to_string)

        useful_list = []
        for elem in soup.descendants:
            if isinstance(elem, PreformattedString):
                continue
            if isinstance(elem, NavigableString):
                content = elem.output_ready().strip().replace('\n', ' ')
                if content:
                    text = textwrap.fill(normalize_entities(content), self.width)
                    useful_list.append(' ' + text)
        return ''.join(useful_list).replace('  ', '').replace(' .', '.').strip()

    def _format_body(self, soup):
        format_link(soup)
        tag_to_string(soup, self.tags_to_string)

        useful_list = []
        paragraph = ''

        for elem in soup.descendants:
            if elem.name == 'br' and useful_list[-1] != os.linesep:
                useful_list.append('\n')

            if isinstance(elem, PreformattedString):
                continue

            if isinstance(elem, NavigableString):
                paragraph += ' ' + elem.output_ready().strip().replace('\xa0', ' ')
                paragraph_ = paragraph.replace('  ', ' ').replace(' .', '.').strip()

                if len(paragraph_):
                    ns = elem.next_sibling

                    if isinstance(ns, NavigableString):
                        continue
                    else:
                        if len(useful_list) > 1 and useful_list[-1] != os.linesep:
                            useful_list.append(os.linesep)

                        useful_list.append(textwrap.fill(normalize_entities(paragraph_), self.width))
                        paragraph = ''

                        parent = elem.parent
                        grandparent = parent.parent

                        if any(tag_name in ['p', 'td'] for tag_name in [parent.name, grandparent.name]):
                            useful_list.append(os.linesep)

        if useful_list[-1] == os.linesep:
            del useful_list[-1]

        return ''.join(useful_list)


def format_link(soup):
    for tag in soup.find_all('a'):
        href = tag.attrs.get('href')
        if any(ext in href.lower() for ext in ['javascript', 'onclick']):
            link = tag.get_text(strip=True)
        else:
            link = '{}'.format('{} [{}]'.format(tag.get_text(strip=True), href))
        tag.replace_with(link)


def tag_to_string(soup, *tags):
    for tag in tags:
        for target in soup.find_all(tag):
            target.replace_with(target.get_text(strip=True))


def normalize_entities(text):
    entities = {
        '\u2014': '-',
        '\u2013': '-',
        '&mdash;': '-',
        '&ndash;': '-',
        '\u00A0': ' ',
        '\u00AB': '"',
        '\u00BB': '"',
        '&quot;': '"',
        '&gt;': '>',
        '&lt;': '<',
    }
    for c, r in entities.items():
        text = text.replace(c, r)
    return text
