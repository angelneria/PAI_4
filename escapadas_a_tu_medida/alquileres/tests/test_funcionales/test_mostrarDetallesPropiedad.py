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

class TestMostrarDetallesPropiedad():
  def setup_method(self, method):
    self.driver = webdriver.Chrome()
    self.vars = {}
  
  def teardown_method(self, method):
    self.driver.quit()
  
  def test_mostrarDetallesPropiedad(self):
    self.driver.get("http://localhost:8000/")
    self.driver.set_window_size(1936, 1056)
    self.driver.find_element(By.CSS_SELECTOR, ".col:nth-child(1) .card-img-top").click()
  
