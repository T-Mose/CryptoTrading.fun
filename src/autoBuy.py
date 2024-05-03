from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def handle_bought_coin(coin):
    pump_fun_link = f"https://pump.fun/{coin['mint']}"
    
    # Configure Chrome options
    options = Options()
    options.add_experimental_option("detach", True)

    # Set up ChromeDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Open the pump.fun link
    driver.get(pump_fun_link)

    driver.maximize_window()

    # Locate the button with the text "1 sol" within the specific div
    button_1_sol = driver.find_element_by_xpath("//div[contains(@class, 'flex flex-col')]//button[text()='1 sol']")
    button_1_sol.click()

    # Locate the button with class "inline-flex" and click it
    button_inline_flex = driver.find_element_by_class_name("inline-flex")
    button_inline_flex.click()











