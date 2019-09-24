def test_sqlparse():
    import sqlparse
    raw = 'select * from foo; select * from bar;'
    statements = sqlparse.split(raw)
    print(statements)
