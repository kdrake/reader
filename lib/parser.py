import re

from bs4 import BeautifulSoup


def compile_pattern(elements):
    return re.compile('|'.join([re.escape(e.lower()) for e in elements]), re.I)


class ParseResult:
    def __init__(self, title, content):
        self.title = title
        self.content = content


class Parser:
    def __init__(self, cfg):
        self.cfg = cfg
        self._candidates = {}
        self.regexps = {
            'unlikely_candidates': compile_pattern(self.cfg.get('unlikely_candidates')),
            'positive': compile_pattern(self.cfg.get('positive')),
            'negative': compile_pattern(self.cfg.get('negative')),
            'div_to_p_elements': re.compile("<(a|blockquote|dl|div|img|ol|p|pre|table|ul)", re.I),
        }

    def get_article(self, text):
        soup = BeautifulSoup(text, 'lxml')

        title = self._get_title(soup)
        content = self._get_article(soup)

        return ParseResult(title, content)

    def _get_title(self, soup):
        for tag in self.cfg.get('title_tags'):
            tag = soup.find(tag)
            if tag is not None:
                return tag

    def _get_article(self, soup):
        rm_tags(soup, 'script', 'style', 'object', 'iframe')

        self._rm_unlikely_candidates(soup)
        self._transform_misused_divs_into_paragraphs(soup)

        # Проставим оценки элементам content_tags и сформируем словарь наиболее подходящих элементов
        self._score_content_tags(soup)

        # Выберем элемент с наибольшим весом
        best_candidate = self._get_best_candidate()
        self._clean_node(best_candidate)

        return best_candidate

    def _score_content_tags(self, soup):
        # Будем считать, что полезный контент содержится в элементах content_tags
        for tag in self.cfg.get('content_tags'):
            for node in soup.find_all(tag):
                # Обычно элементы p распологают внутри других блочных элементов, образую вместе "важный" контент
                parent_node = node.parent
                if parent_node is None:
                    continue

                inner_text = node.get_text(strip=True)
                inner_text_len = len(inner_text)
                # Если внутренний контент элемента p меньше min_text_length, то не будем учитывать данный элемент
                if inner_text_len < self.cfg.get('min_text_length'):
                    continue

                parent_hash = hash(str(parent_node))
                if parent_hash not in self._candidates:
                    self._candidates[parent_hash] = self._init_candidate(parent_node)

                content_score = 1
                # Добавим очков с учетом количества частей текста, разделенного запятыми
                content_score += len(inner_text.split(','))

                self._candidates[parent_hash]['score'] += content_score

        # В качественном контенте плотность ссылок должна быть невысокой, учтем это.
        for k in self._candidates:
            candidate = self._candidates[k]
            link_density = get_link_density(candidate['node'])
            candidate['score'] *= (1 - link_density)

    def _init_candidate(self, node):
        """
        Создаем объект candidate и задаем ему вес на основе имени и класса элемента
        """
        content_score = 0

        if node.name == 'div':
            content_score += 5
        elif node.name == ['pre', 'td', 'blockquote']:
            content_score += 3
        elif node.name == ['address', 'ol', 'ul', 'dl', 'dd', 'dt', 'li', 'form']:
            content_score -= 3
        elif node.name == ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'th']:
            content_score -= 5

        content_score += self._get_class_weight(node)

        return {'score': content_score, 'node': node}

    def _get_class_weight(self, node):
        """
        Возвращает вес node с учетом названий его атрибутов id и class
        """
        total_weight = 0

        positive_weight = self.cfg.get('positive_weight')
        negative_weight = self.cfg.get('negative_weight')

        if 'class' in node:
            if self.regexps['negative'].search(node['class']):
                total_weight -= negative_weight
            if self.regexps['positive'].search(node['class']):
                total_weight += positive_weight

        if 'id' in node:
            if self.regexps['negative'].search(node['id']):
                total_weight -= negative_weight
            if self.regexps['positive'].search(node['id']):
                total_weight += positive_weight

        return total_weight

    def _get_best_candidate(self):
        sorted_candidates = sorted(self._candidates.values(), key=lambda x: x['score'], reverse=True)
        return sorted_candidates[0]['node']

    def _rm_unlikely_candidates(self, soup):
        for node in soup.find_all(True):
            attr_string = '{} {}'.format(node.get('id', ''), ''.join(node.get('class', '')))
            if len(attr_string) < 2:
                continue
            if self.regexps['unlikely_candidates'].search(attr_string) and node.name != 'body':
                node.extract()

    def _transform_misused_divs_into_paragraphs(self, soup):
        for node in soup.find_all('div'):
            if self.regexps['positive'].search(' '.join(node.get('class', ''))):
                node.name = 'p'
            if not self.regexps['div_to_p_elements'].search(node.decode_contents()):
                node.name = 'p'

    def _clean_node(self, node):
        # Удаляем лишние элементы внутри node
        rm_tags(node, 'script', 'noscript', 'style', 'h1', 'object', 'img', 'iframe')
        # Очистим node от лишних внутренних элементов с учетом правил
        self._clean_conditionally(node, 'form', 'table', 'ul', 'div', 'p', 'a')
        # Очищаем элементы внутри node от атрибутов и инлайн стилей
        clean_style(node)

    def _clean_conditionally(self, element, *tags):
        for tag in tags:
            for node in element.find_all(tag):

                content_length = len(node.get_text(strip=True))
                if not content_length:
                    node.extract()

                # Значимость отдельно взятого элемента
                node_weight = self._get_class_weight(node)

                hash_node = hash(str(node))
                if hash_node in self._candidates:
                    content_score = self._candidates[hash_node]['score']
                else:
                    content_score = 0

                if node_weight + content_score < 0:
                    node.extract()
                else:
                    link_density = get_link_density(node)
                    positive_weight = self.cfg.get('positive_weight')

                    to_remove = False
                    if node_weight < positive_weight and link_density > self.cfg.get('min_link_density'):
                        # Малая значимость и плотность ссылок > min_link_density
                        to_remove = True
                    elif node_weight >= positive_weight and link_density > self.cfg.get('max_link_density'):
                        # "Хорошая" значимость, но плотность ссылок > max_link_density
                        to_remove = True

                    if to_remove:
                        node.extract()


def get_link_density(soup):
    """
    Возвращает коэффициент плотности ссылок в тексте. Чем меньше, тем "качественнее" текст.
    """
    text_length = len(soup.get_text(strip=True))
    if text_length == 0:
        return 0

    link_length = 0
    for link in soup.find_all('a'):
        link_length += len(link.get_text(strip=True))

    return link_length / text_length


def rm_tags(soup, *tags):
    for tag in tags:
        for target in soup.find_all(tag):
            target.extract()


def clean_style(soup):
    for node in soup.find_all(True):
        del node['class']
        del node['id']
        del node['style']
