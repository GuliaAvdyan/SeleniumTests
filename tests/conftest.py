import logging
import pytest
from selenium import webdriver
import datetime
from selenium.webdriver.chrome.options import Options


def pytest_addoption(parser):
    parser.addoption("--cmdopt", action="store", default='s2')
    parser.addoption("-E", action="store", metavar="NAME",
                     help="only run tests matching the environment NAME.")
    parser.addoption(
        "--localdriver", action="store_true", default=False,
        help="run tests on local machine")
    parser.addoption("--widget", action="store", default="default name")
    parser.addoption('--settings', action='store', default='settings.json')


def pytest_configure(config):
    # register an additional marker
    config.addinivalue_line(
        "markers", "env(name): mark test to run only on named environment")


@pytest.fixture
def cmdopt(request):
    return request.config.getoption("--cmdopt")


@pytest.fixture
def localdriver(request):
    return request.config.getoption("--localdriver")


@pytest.fixture
def some_widget(request):
    return request.config.getoption("--widget")


@pytest.fixture
def settings(request):
    return request.config.getoption("--settings")


@pytest.fixture(scope="session")
def browser():
    options = Options()
    options.add_argument('--window-size=1920,1080')
    # options.headless = True

    driver = webdriver.Chrome(options=options, executable_path='/home/eugryumova/chromedriver/chromedriver')

    # driver = webdriver.Remote(                 # for docker mode
    #     command_executor='http://4444:4444/wd/hub',
    #     desired_capabilities=DesiredCapabilities.CHROME)

    yield driver
    driver.quit()


@pytest.fixture(scope='module')
def logger():
    logger = logging.getLogger('sgd_svrg')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    fh = logging.FileHandler(f'logs/{datetime.datetime.now().strftime("%Y_%m_%d_%M_%S_%f")}.log')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger