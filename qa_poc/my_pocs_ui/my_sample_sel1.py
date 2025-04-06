# Python program to demonstrate
# selenium
  
# import webdriver
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

  
# create webdriver object
driver = webdriver.Chrome()
  
# get google.co.in
driver.get("https://google.co.in")
search_bar = driver.find_element("name","q")
search_bar.clear()
search_bar.send_keys("getting started with python")
sleep(5)
search_bar.clear()
search_bar.send_keys("getting started with selenium")
search_bar.send_keys(Keys.RETURN)
print(driver.current_url) 
driver.close()