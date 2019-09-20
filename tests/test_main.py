# First test case for the main function

from pytest import raises
from st2g.main import main


def test_main_with_no_arg():
    main([])


def test_main_asking_version():
    with raises(SystemExit):
        main("-v")


def test_main_help():
    with raises(SystemExit):
        main("-h")
