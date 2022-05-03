import urllib.parse, os, requests, sys

from pathlib import Path
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

wait_time = 30


# Starts morningstar driver and configre the page for getting the data correct
def start_driver_morningstar():
    chrome_options = Options()
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument('--log-level=3')
    driver = webdriver.Chrome(ChromeDriverManager().install(),options=chrome_options)

    driver.get('https://www.morningstar.es')


    pop_up = WebDriverWait(driver, wait_time).until(EC.element_to_be_clickable(
        (By.XPATH, '//*[@id="onetrust-accept-btn-handler"]')))
    pop_up.send_keys("\n")

    pop_up2 = WebDriverWait(driver, wait_time).until(EC.element_to_be_clickable(
        (By.XPATH, '//*[@id="btn_individual"]')))
    pop_up2.send_keys("\n")

    return driver

# Gets fund morningstar ID from real fund code
def get_fund_id(fund_id, driver):
    search_box = driver.find_element_by_css_selector('#quoteSearch')
    search_box.send_keys(Keys.CONTROL + "a")
    search_box.send_keys(Keys.DELETE)
    search_box.send_keys(fund_id)

    fund_name = WebDriverWait(driver, wait_time).until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, '.ac_odd')))
    fund_name.click()

    url = driver.current_url
    return url.split('id=')[-1]

# Gets fund name and expenses
def get_fund_info(driver):
    fund_name = get_fund_name(driver)
    expenses = get_fund_expenses(driver)
    return fund_name, expenses


def get_fund_name(driver):
    fund_name = WebDriverWait(driver, wait_time).until(EC.element_to_be_clickable(
        (By.XPATH, '//*[@id="snapshotTitleDiv"]/table/tbody/tr/td/div/h1')))
    return fund_name.text


def get_fund_expenses(driver):
    expenses = WebDriverWait(driver, wait_time).until(EC.element_to_be_clickable(
        (By.XPATH, '//*[@id="overviewQuickstatsDiv"]/table/tbody/tr[9]/td[3]')))
    return float(expenses.text.strip('%').replace(",", "."))

# Gets info from morningstar given and array of funds 
def get_funds_info_from_morningstar(fund_ids):
    driver = start_driver_morningstar()
    funds = []

    for fund_id in fund_ids:
        try:
            id = get_fund_id(fund_id, driver)
        except:
            return "Error executing the script, please try again"
        name, expenses = get_fund_info(driver)

        fund = {}
        fund['id'] = id
        fund['name'] = name
        fund['expenses'] = expenses
        funds.append(fund)

    driver.close()
    return funds


# Constructs the pdf given an array of fund ids and percentages
def call_pdf_url(funds_ids, percents):
    funds = combined(funds_ids)
    percents = combined(percents)
    strs = ["FO" for x in range(len(funds_ids))]
    strs = combined(strs)

    getVars = {'securityIds': funds,
               'marketValues': percents, 'typeids': strs}
    url = 'https://lt.morningstar.com/j2uwuwirpv/xraypdf/default.aspx?LanguageId=es-ES&CurrencyId=EUR&'

    url = url + urllib.parse.urlencode(getVars)
    return url

def combined(values):
    symbol = '|'
    combined = ''
    for value in values:
        combined += str(value) + symbol
    return combined

def save_pdf(url):
    filename = Path('xray.pdf')
    response = requests.get(url)
    filename.write_bytes(response.content)
    return filename


if __name__ == "__main__":
    # call the driver
    print("GETTING FUND IDs...")
    driver = start_driver_morningstar()

    # made two arrays for IDs and percentages
    arguments =  sys.argv[1:]
    fund_ids = arguments[0::2]
    percentages = arguments[1::2]

    # get the morningstar IDs
    morningstar_ids = []
    for fund_id in fund_ids:
        id = get_fund_id(fund_id, driver)
        morningstar_ids.append(id)
   
    driver.close()
    driver.quit()

    # save and open the x-ray
    print("GENERATING PDF...")
    url = call_pdf_url(morningstar_ids,percentages)
    save_pdf(url)
    os.system('xray.pdf')
