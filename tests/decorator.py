
import time


SLEEPING_TIME = 6


def sleep_decorator(func):
    """Decorator that improves testing stability.
    You can modify total sleeping time by changing
    global variable SLEEPING_TIME in decorators module"""

    def wrapper(*args, **kwargs):
        time.sleep(SLEEPING_TIME/2)
        func(*args, **kwargs)
        time.sleep(SLEEPING_TIME/2)

    return wrapper



# search_the_leads_button_and_move
search_for_button_on_a_page("//*[@id='nav_menu']/div[2]/a/div[1]")

# search_the_button_first_voronka
search_for_button_on_a_page("//*[@id='aside__list-wrapper']/ul/li[1]/a")
click_the_button("//*[@id='aside__list-wrapper']/ul/li[1]/a")
time.sleep(2)

click_the_button('//*[@id="list__body-right"]/div[1]/div[3]/a[2]/span[2]')
search_for_button_on_a_page('//*[@id="person_n"]')
