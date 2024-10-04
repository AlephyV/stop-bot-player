import json
import time
from selenium.webdriver.support import expected_conditions as EC
import openai
import asyncio
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

SPANS_SELECTOR = 'div.ct.answers.up-enter-done div label>span'
API_KEY = ''
URL = 'https://stopots.com/system/'
AI_SYSTEM_INSTRUCTIONS = "As categorias estão separadas por virugla: [Teste, cor ou rosa] considere que mesmo tendo um [ou] é somente uma categoria. Retorne tudo maiusculo. Se houver acentuação mantenha. A chave do json deve ser exatamente a categoria recebida, sem alteração de texto se receber ABCGoiaba retornar ABCGoiaba."
AI_USER_INSTRUCTIONS = "Estou jogando STOP ou adedonha. A letra é {0} e as categorias são {1} me retorne as respostas em formato json. Lembre-se a primeira letra da palavra deve ser a indicada."

def get_spans(driver):
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, SPANS_SELECTOR))
    )
    
    spans = driver.find_elements(By.CSS_SELECTOR, SPANS_SELECTOR)
    
    return spans

def format_text(text):
    text = text.text.strip()
    if "\n" in text:
        text = text.split("\n")[1]
    text = text.replace(",", "")
    text = text.upper()

    return text

def get_filtered_spans(spans):
    unique_spans = set()
    filtered_spans = []

    for span in spans:
        span_text = format_text(span)

        if span_text not in unique_spans:
            unique_spans.add(span_text)
            filtered_spans.append(span)

    return filtered_spans

def get_categories_from_spans(spans):
    categories = []

    for span in spans:
        category = format_text(span)
        categories.append(category)

    return categories

def extract_categories(driver):
    spans = get_spans(driver)
    filteredSpans = get_filtered_spans(spans)
    return get_categories_from_spans(filteredSpans)

def extract_letter(html):
    soup = BeautifulSoup(html, 'html.parser')
    letter = soup.select_one('#letter span').get_text(strip=True)
    return letter

async def get_answers(api_key, letter, categories):
    client = openai.OpenAI(api_key=api_key)
    
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{ 'role': 'user', 'content': AI_USER_INSTRUCTIONS.format(letter, ', '.join(categories)) }, {"role": "system", "content": AI_SYSTEM_INSTRUCTIONS}]
    )

    return completion.choices[0].message.content

def mock_answers():
    return """
    {
        "Super-Herói": "Pantera Negra",
        "Esportista": "Pelé",
        "Sobrenome": "Pereira",
        "Time Esportivo": "Paris Saint-Germain",
        "Vestuário": "Pijama",
        "Instrumento Musical": "Piano",
        "Filme": "Pulp Fiction",
        "Game": "Pokémon",
        "Remédio": "Paracetamol",
        "Série": "Prison Break",
        "Eletro Eletrônico": "PlayStation",
        "Fruta Legume ou Verdura": "Pêssego"
    }
    """.upper()

def configure_driver(url):
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    driver.get(url)

    return driver

def fill_inputs(categories, answers, driver):
    spans = get_spans(driver)
    filtered_spans = get_filtered_spans(spans)

    for span in filtered_spans:
        next_element = span

        while next_element and next_element.tag_name != 'input':
            next_element = driver.execute_script("return arguments[0].nextElementSibling;", next_element)

        if next_element:
            category = format_text(span)

            if any(category in cat for cat in categories):
                answer = answers.get(category, "")

                actions = ActionChains(driver)
                actions.move_to_element(next_element).click().perform()
                time.sleep(0.2)

                next_element.send_keys(answer)
                time.sleep(0.1)

async def process(url = 'https://stopots.com/system/'):
    driver = configure_driver(url)

    input("Inicie o STOP então aperte enter\n")

    continuar = "Y"
    while continuar == 'Y':
        categories = extract_categories(driver)
        letter = extract_letter(driver.page_source)
        
        answersString = await get_answers(API_KEY, letter, categories)
        answers = json.loads(answersString)

        fill_inputs(categories, answers, driver)
        
        continuar = input("Y/N?\n")

    input("waiting...\n")


if __name__ == "__main__":
    asyncio.run(process(URL))