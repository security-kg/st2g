# First test case for the main function

import os, pytest
from pytest import raises
from st2g.main import main


def test_main_with_no_arg():
    with raises(SystemExit):
        main([])


def test_main_asking_version():
    with raises(SystemExit):
        main("-v")


def test_main_help():
    with raises(SystemExit):
        main("-h")


def test_main_process():
    if not os.path.exists("examples/data/demo") or not os.path.exists("examples/data/TC"):
        pytest.skip("skipping tests without TC", allow_module_level=True)
    main("run --input examples/data/demo/1.txt --output temp/collect/demo_1")
    main("run --input examples/data/demo/2.txt --output temp/collect/demo_2")
    main("run --input examples/data/TC/TC_C_1.txt --output temp/collect/tc_1")
    main("run --input examples/data/TC/TC_C_2.txt --output temp/collect/tc_2")
    main("run --input examples/data/TC/TC_C_3.txt --output temp/collect/tc_3")
    main("run --input examples/data/TC/TC_C_3_2.txt --output temp/collect/tc_3_2")
    main("run --input examples/data/TC/TC_C_4.txt --output temp/collect/tc_4")
    main("run --input examples/data/TC/TC_C_5.txt --output temp/collect/tc_5")
