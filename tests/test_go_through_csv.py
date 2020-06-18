import os
import csv
import pytest
from functools import reduce
from pprint import pprint


class TestProcessCSV:
    csv_path = reduce(os.path.join, ['.', 'examples', 'data', 'sql_dump', 'blogs_data_p.csv'])
    if not os.path.exists(csv_path):
        pytest.skip("skipping tests without articles", allow_module_level=True)

    def test_process_csv_articles(self, num=1000000):
        articles = []
        from st2g.process import process_raw_text, output_result
        with open(TestProcessCSV.csv_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            to_fetch = num + 1
            print("Total: {}".format(68454))
            for i, row in enumerate(reader):
                if i == 0:
                    header: list = row
                else:
                    article = (row[header.index('title')], row[header.index('content')])
                    articles.append(article)
                    result = process_raw_text(article[1])
                    if result['evidence']:
                        output_result(result, "temp/go_through_all/{}.gv".format(i))
                if i >= to_fetch:
                    break
                if i % 100 == 99:
                    print("Processed: {}".format(i))
