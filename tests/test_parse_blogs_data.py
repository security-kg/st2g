import os
import pytest
from functools import reduce


class TestReadBlog:
    data_dir = reduce(os.path.join, [".", "examples", "data", "sql_dump"])
    data_source = os.path.join(data_dir, "blogs_data_p.sql")
    data_cache = os.path.join(data_dir, "blogs_data_p.csv")
    if not os.path.exists(data_source):
        pytest.skip("skipping tests without Blog source data", allow_module_level=True)

    def test_data_source(self):
        print("PATH: ", TestReadBlog.data_source)
        assert os.path.exists(TestReadBlog.data_source)

    @pytest.mark.skip(reason="Only need to do this once (come to think about it, it's actually not a test)")
    def test_parse_source(self):
        import sqlparse
        with open(TestReadBlog.data_source) as fin:
            raw_data = fin.read()
        sql_data = sqlparse.parse(raw_data)
        insert_data = []
        keys = ['table', 'id', 'title', 'author', 'content', 'date', 'url', 'pic_path', 'pic_info']
        for sql in sql_data:
            if sql.get_type() != "INSERT":
                print("------EXCEPTION------\n", str(sql))
                continue
            table_name = sql.get_name()[1:-1]
            values = [_ for _ in sql if isinstance(_, sqlparse.sql.Values)][0].get_sublists()
            values = [[_ for _ in v][1] for v in values]  # skip Punctuation
            values = [[_.value
                       for _ in v if str(_.ttype) not in ["Token.Punctuation", "Token.Text.Whitespace"]
                       ] for v in values]  # extract specific values
            # `id`, `title`, `author`, `content`, `date`, `url`, `pic_path`, `pic_info`
            # values = [dict(zip(keys, v)) for v in values] # add keys / no use to csv convertion
            values = [[table_name] + v for v in values]
            insert_data = insert_data + values
        import csv
        with open(TestReadBlog.data_cache, 'w', newline='') as fout:
            writer = csv.writer(fout)
            writer.writerow(keys)
            for v in insert_data:
                writer.writerow(v)
