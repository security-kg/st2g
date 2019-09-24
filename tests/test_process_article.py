import os
import csv
import pytest
from functools import reduce
from pprint import pprint


class TestArticle:
    csv_path = reduce(os.path.join, ['.', 'examples', 'data', 'sql_dump', 'blogs_data_p.csv'])

    @pytest.fixture
    def first_ten_article(self, num=10):
        articles = []
        with open(TestArticle.csv_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            to_fetch = num + 1
            for i, row in enumerate(reader):
                if i == 0:
                    header: list = row
                else:
                    articles.append((row[header.index('title')], row[header.index('content')]))
                if i >= to_fetch:
                    break
        return articles

    def test_load_article(self, first_ten_article):
        pprint(("title: ", first_ten_article[0][0]))
        pprint(("content: ", first_ten_article[0][1]))

    def test_process_first_article(self, first_ten_article):
        from st2g.process import process_raw_text
        result = process_raw_text(first_ten_article[0][1])
        pprint(("title: ", first_ten_article[0][0]))
        pprint([{"sent": sent, "ents": sent.ents} for sent in result['doc'].sents if sent.ents])
        dot = result['dot']
        dot.render('temp/first_article.gv')

    def test_process_first_ten_article(self, first_ten_article):
        from st2g.process import process_raw_text, output_result
        for i, (title, content) in enumerate(first_ten_article):
            result = process_raw_text(content)
            output_result(result, "temp/{}.gv".format(i))
