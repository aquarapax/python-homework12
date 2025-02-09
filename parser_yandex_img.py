import os
import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import quote

# Константы
URL =    "https://yandex.ru/images/search"  #  
DELAY = 2  # Задержка между запросами (в секундах)
DATASET_DIR = "dataset"
MAX_IMAGES_PER_CLASS = 1000
IMAGE_CLASSES = ["polar bear", "brown bear"]
PROXY_FILE = "proxy_list.txt"  # Файл с прокси
USER_AGENT_FILE = "user_agent.txt"  # Файл с User-Agent

# Загрузка прокси из файла
def load_proxies():
    if os.path.exists(PROXY_FILE):
        with open(PROXY_FILE, "r") as file:
            proxies = file.read().splitlines()
        return proxies
    else:
        print(f"Файл {PROXY_FILE} не найден. Прокси не будут использоваться.")
        return []

# Загрузка User-Agent из файла
def load_user_agents():
    if os.path.exists(USER_AGENT_FILE):
        with open(USER_AGENT_FILE, "r") as file:
            user_agents = file.read().splitlines()
        return user_agents
    else:
        print(f"Файл {USER_AGENT_FILE} не найден. Будет использован стандартный User-Agent.")
        return ["Mozilla/5.0"]

# Инициализация браузера с прокси и User-Agent
def init_browser(proxy=None, user_agent=None):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Запуск в фоновом режиме
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    if proxy:
        chrome_options.add_argument(f"--proxy-server={proxy}")
    if user_agent:
        chrome_options.add_argument(f"--user-agent={user_agent}")

    servico = ChromeService(executable_path=ChromeDriverManager().install())
    navegador = webdriver.Chrome(service=servico, options=chrome_options)
    return navegador

# Создание директории
def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Скачивание изображения
def download_image(image_url, save_path):
    try:
        response = requests.get(image_url, timeout=10)
        if response.status_code == 200:
            with open(save_path, "wb") as file:
                file.write(response.content)
            return True
    except Exception as e:
        print(f"Ошибка при загрузке изображения: {e}")
    return False

# Получение URL изображений
def fetch_image_urls(query, max_images, proxies, user_agents):
    image_urls = set()
    page = 0

    while len(image_urls) < max_images:
        # Выбор случайного прокси и User-Agent
        proxy = random.choice(proxies) if proxies else None
        user_agent = random.choice(user_agents) if user_agents else None

        # Инициализация браузера
        navegador = init_browser(proxy, user_agent)
        print(f"Используется прокси: {proxy}, User-Agent: {user_agent}")

        # Формируем URL для поиска
        search_url = f"{URL}?p={page}&text={quote(query)}"
        print(f"Загрузка страницы: {search_url}")

        try:
            # Открываем страницу в браузере
            navegador.get(search_url)
            time.sleep(DELAY)  # Ждем загрузки страницы

            # Ищем все элементы с изображениями
            images = navegador.find_elements(By.CLASS_NAME, "ImagesContentImage-Image_clickable")

            # Переходим на страницу каждого изображения и извлекаем URL
            for img in images:
                if len(image_urls) >= max_images:
                    break

                try:
                    # Кликаем на изображение, чтобы открыть его страницу
                    img.click()
                    time.sleep(DELAY)  # Ждем загрузки страницы с изображением

                    # Ищем URL полноразмерного изображения
                    full_image = navegador.find_element(By.CLASS_NAME, "MMImage-Origin")
                    image_url = full_image.get_attribute("src")

                    if image_url and image_url.startswith("http"):
                        image_urls.add(image_url)
                        print(f"Найдено изображение: {image_url}")

                    # Возвращаемся на страницу поиска
                    navegador.back()
                    time.sleep(DELAY)
                except (NoSuchElementException, TimeoutException) as e:
                    print(f"Ошибка при обработке изображения: {e}")
                    continue

            # Переход на следующую страницу
            page += 1
        except Exception as e:
            print(f"Ошибка при загрузке страницы: {e}")
        finally:
            navegador.quit()  # Закрываем браузер после каждого запроса

    return list(image_urls)

# Скачивание изображений для класса
def download_images_for_class(class_name, max_images, proxies, user_agents):
    class_dir = os.path.join(DATASET_DIR, class_name)
    create_directory(class_dir)

    # Получение URL изображений
    print(f"Поиск изображений для класса: {class_name}")
    image_urls = fetch_image_urls(class_name, max_images, proxies, user_agents)

    # Скачивание изображения
    for idx, image_url in enumerate(image_urls):
        if idx >= max_images:
            break
        file_name = f"{idx:04d}.jpg"  # Форматируем имя файла (0000, 0001, ..., 0999)
        save_path = os.path.join(class_dir, file_name)
        print(f"Скачивание изображения {idx + 1}/{max_images}: {image_url}")
        if not download_image(image_url, save_path):
            print(f"Не удалось скачать изображение: {image_url}")

# Основная функция
def main():
    proxies = load_proxies()
    user_agents = load_user_agents()

    for class_name in IMAGE_CLASSES:
        download_images_for_class(class_name, MAX_IMAGES_PER_CLASS, proxies, user_agents)
# Тест
if __name__ == "__main__":
    main()