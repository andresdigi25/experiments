from selenium_driver_updater import DriverUpdater
from selenium import webdriver
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
filename = DriverUpdater.install(path=base_dir, driver_name=DriverUpdater.chromedriver, upgrade=True, check_driver_is_up_to_date=True, old_return=False)
#driver = webdriver.Chrome(filename)
driver = webdriver.Chrome()
driver.get('https://google.com')