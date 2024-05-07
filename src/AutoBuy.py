from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.chrome.service import Service





def handle_bought_coin(coin):
    pump_fun_link = f"https://pump.fun/{coin['mint']}"
    
    # Configure Chrome options
    options = Options()
    options.add_experimental_option("detach", True)

    # Set up ChromeDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # Open the pump.fun link
        driver.get(pump_fun_link)
        
        # Maximize window
        driver.maximize_window()

        # Explicitly wait for the "1 sol" button to be clickable
        button_1_sol = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'flex flex-col')]//button[text()='1 sol']")))
        button_1_sol.click()

        # Explicitly wait for the "inline-flex" button to be clickable
        button_inline_flex = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "inline-flex")))
        button_inline_flex.click()
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")

    finally:
        # Close the WebDriver instance
        driver.quit()
