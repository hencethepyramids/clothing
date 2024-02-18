import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

retry_count = 0
max_retries = 5

amazon_product_url = "https://www.amazon.com/s?k=ralph+lauren+polo+sweaters+for+men&crid=OTOFQ647XI0P&sprefix=ralph+lauren+polo+sweaters+for+men%2Caps%2C563&ref=nb_sb_noss_1"
ralph_product_url = "https://www.ralphlauren.com/men-clothing-sweaters/r/polo-ralph-lauren"
poshmark_product_url = "https://poshmark.com/search?query=ralph%20lauren%20polo%20sweaters%20men&type=listings&src=dir"
macys_product_url = "https://www.macys.com/shop/featured/ralph%20lauren%20mens%20polo%20sweaters"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299"
}

def fetch_html(url):
    global retry_count

    while retry_count < max_retries:
        try:
            page = requests.get(url, headers=headers, timeout=10)
            if page.status_code == 503:
                print(f"503 Server Error: Service Unavailable for url: {url} Retry #{retry_count + 1}")
                retry_count += 1
                time.sleep(2**retry_count)
                continue
            page.raise_for_status()  # Raise an error for unsuccessful requests
            retry_count = max_retries  # Reset retry_count
            return page.content
        except requests.RequestException as e:
            retry_count += 1
            print(f"Error while fetching {url}: {str(e)} Retry #{retry_count}")
            if retry_count == max_retries:
                return None  # Return None if max retries reached
            time.sleep(2**retry_count)

    return None  # Return None if max retries reached


def fetch_and_parse(url):
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    # Extract the product price and title
    if "amazon" in url:
        title_element = soup.find("span", {"class": "a-size-medium"})
        price_element = soup.find("span", {"class": "a-price"})

        if title_element and price_element:
            title = title_element.text.strip()
            price = price_element.text.strip().replace("$", "").replace(",", "")
            price = float(price) if price else "Price not found"
        else:
            title = "Title not found"
            price = "Price not found"
    elif "ralphlauren" in url:
        # Use Selenium for dynamic content
        options = Options()
        options.headless = True
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(5)  # Wait for dynamic content to load
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        title_element = soup.find("h1", {"class": "product-title"})
        price_element = soup.find("span", {"class": "price"})

        title = title_element.text.strip() if title_element else "Title not found"
        price = price_element.text.strip() if price_element else "Price not found"
    elif "poshmark" in url:
        title_element = soup.find("h1", {"class": "styles__Title-sc-1ynbvzw-0 styles__h1Title-sc-1ynbvzw-2 gUtkkP"})
        price_elements = soup.find_all("span", {"class": "ItemPrice_price__2xTlM"})
        price = [float(price_element.text.strip().replace("$", "")) for price_element in price_elements]
    elif "macys" in url:
        title_element = soup.find("h1", {"class": "product-title"})
        price_element = soup.find("span", {"class": "price-value"})

        title = title_element.text.strip() if title_element else "Title not found"
        price = price_element.text.strip() if price_element else "Price not found"

    if "poshmark" not in url:
        price = price if price else "Price not found"
        price = [price] if not isinstance(price, list) else price
    else:
        price = price if price else "Price not found"

    return {"title": title, "price": price}

def compare_prices(products):
    lowest_price = min(product["price"] for product in products if product["price"] != "Price not found")
    matching_products = [product for product in products if product["price"] == lowest_price]

    for product in matching_products:
        print(f"The lowest price for {product['title']} is: ${product['price']}")

products = [
    fetch_and_parse(amazon_product_url),
    fetch_and_parse(ralph_product_url),
    fetch_and_parse(poshmark_product_url),
    fetch_and_parse(macys_product_url),
]

compare_prices(products)
