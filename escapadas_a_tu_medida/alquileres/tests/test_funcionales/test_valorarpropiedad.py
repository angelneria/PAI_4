# Generated by Selenium IDE
import pytest
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC

class TestValorarpropiedad():
  def setup_method(self, method):
    self.driver = webdriver.Chrome()
    self.vars = {}
  
  def teardown_method(self, method):
    self.driver.quit()
  
  def test_valorarpropiedad(self):
    self.driver.get("http://localhost:8000/")
    self.driver.set_window_size(1936, 1056)
    WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Registro"))
        )
    self.driver.find_element(By.LINK_TEXT, "Login").click()
    self.driver.find_element(By.ID, "username").send_keys("Manuvele")
    self.driver.find_element(By.ID, "password").send_keys("pepe")
    self.driver.find_element(By.CSS_SELECTOR, ".btn-custom").click()
    self.driver.find_element(By.CSS_SELECTOR, ".col:nth-child(1) .card-img-top").click()
    element = WebDriverWait(self.driver, 10).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "label:nth-child(2)"))
)
    self.driver.execute_script("arguments[0].click();", element)

    element = WebDriverWait(self.driver, 10).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-primary"))
)
    self.driver.execute_script("arguments[0].click();", element)

    
  
