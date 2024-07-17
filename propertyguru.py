import os
import pandas as pd
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

file_path = r"C:\Users\jessi\OneDrive\Desktop\PropertyGuru data\housing_data.xlsx"
base_url = "https://www.propertyguru.com.sg/property-for-sale"
url_params_list = [
    "?market=residential&listing_type=sale&freetext=parvis&search=true",
    "?market=residential&listing_type=sale&freetext=waterfall+gardens&search=true",
    "?market=residential&listing_type=sale&freetext=rivergate&search=true"
]
chromedriver_path = r"C:\chromedriver\chromedriver-win32\chromedriver.exe"

def setup_driver():
    options = Options()
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
    options.add_argument(f"user-agent={user_agent}")
    s = Service(executable_path=chromedriver_path)
    return webdriver.Chrome(service=s, options=options)

def extract_record(item):
    record = {}
    try:
        nav_link = item.find('a', {'class': 'nav-link'})
        record['Title'] = nav_link.get('title', 'No Title').replace('For Sale - ', '') if nav_link else 'No Title'
        price_info = item.find('li', {'class': 'list-price'})
        record['Price'] = price_info.find('span', {'class': 'price'}).get_text(strip=True) if price_info else 'No Price'
        area_info = item.find('li', {'class': 'listing-floorarea'})
        record['Area'] = area_info.get_text(strip=True) if area_info else 'No Area'
        recency_info = item.find('div', {'class': 'listing-recency'})
        record['Recency'] = recency_info.get_text(strip=True) if recency_info else 'No Recency'
        record['URL'] = nav_link.get('href', 'No URL') if nav_link else 'No URL'
        return record
    except Exception as e:
        print("An error occurred while extracting record:", e)
        return None

all_records = []

for url_params in url_params_list:
    current_page = 1
    valid_page = True

    while valid_page:
        driver = setup_driver()
        try:
            driver.get(f"{base_url}/{current_page}{url_params}")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="listing-card listing-id"]')))
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            all_results = soup.select('div[class*="listing-card listing-id"]')
            results = [item for item in all_results if 'promoted' not in item['class']]

            if not results:
                valid_page = False
                print(f"No listings or end of listings for {url_params}.")
                continue

            for item in results:
                record = extract_record(item)
                if record:
                    all_records.append(record)

            print(f"Processed page {current_page} for {url_params}")

            # Check for next page
            next_button = soup.select_one('a[class*="pagination-next"]')
            if next_button and 'disabled' not in next_button.get('class', []):
                current_page += 1
            else:
                valid_page = False
                print("No more pages.")

        except Exception as e:
            print("An error occurred:", e)
            valid_page = False

        finally:
            driver.quit()

df = pd.DataFrame(all_records)
df.to_excel(file_path, index=False)
print("Data saved to Excel.")
