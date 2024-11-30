import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys

class TestRegistro():
    def setup_method(self, method):
        self.driver = webdriver.Chrome()
        self.vars = {}

    def teardown_method(self, method):
        self.driver.quit()

    def test_registro(self):
        # Abrir la página
        self.driver.get("http://localhost:8000/")
        self.driver.set_window_size(1936, 1056)

        # Esperar hasta que el enlace "Registro" esté disponible
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Registro"))
        )
        self.driver.find_element(By.LINK_TEXT, "Registro").click()
        self.driver.find_element(By.ID, "id_username").click()
        self.driver.find_element(By.ID, "id_username").send_keys("Jaime")
        self.driver.find_element(By.ID, "id_email").send_keys("jaime.gmarin03@gmail.com")
        self.driver.find_element(By.ID, "id_username").send_keys("Jaime_gomez")
        self.driver.find_element(By.ID, "id_first_name").send_keys("Jaime")
        self.driver.find_element(By.ID, "id_last_name").send_keys("Gomez")
        self.driver.find_element(By.ID, "id_password").send_keys("12345678q")
        self.driver.find_element(By.ID, "id_confirmar_password").send_keys("12345678q")

        # Desplazamiento hacia el campo de teléfono (hacemos scroll explícito)
        telefono_element = self.driver.find_element(By.ID, "id_telefono")
        self.driver.execute_script("arguments[0].scrollIntoView(true);", telefono_element)
        time.sleep(1)  # Esperamos un poco para que el desplazamiento se complete

        # Esperamos a que el campo de teléfono sea visible y se pueda interactuar con él
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of(telefono_element)
        )

        # Escribimos el número de teléfono
        telefono_element.send_keys("64565656565")

        # Desplazamiento hacia el botón y clic con JavaScript (si el clic estándar falla)
        boton_registro = self.driver.find_element(By.CSS_SELECTOR, ".btn")
        self.driver.execute_script("arguments[0].scrollIntoView(true);", boton_registro)  # Desplazamos hacia el botón
        time.sleep(1)  # Esperamos para asegurarnos de que el scroll ha tenido efecto

        # Si el clic falla con Selenium, utilizamos JavaScript para hacer el clic
        self.driver.execute_script("arguments[0].click();", boton_registro)
