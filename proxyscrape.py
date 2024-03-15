from flask import Flask, Response, jsonify, render_template
import requests
import concurrent.futures
import re
import logging
import json
from apscheduler.schedulers.background import BackgroundScheduler
from aiohttp import ClientSession
import asyncio
import datetime
import time

app = Flask(__name__)

LINES_PER_PAGE = 5000
IP_PORT_PATTERN = r"^((25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d):([0-5]?[0-9]{1,4}|6[0-5][0-5][0-3][0-5])$"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

proxies_cache = {
    'http': {},
    'socks4': {},
    'socks5': {}
}

def salvar_proxies_cache():
    with open('proxies_cache.json', 'w') as f:
        json.dump(proxies_cache, f)

def carregar_proxies_cache():
    try:
        with open('proxies_cache.json', 'r') as f:
            global proxies_cache
            proxies_cache = json.load(f)
    except FileNotFoundError:
        logger.info("Arquivo de cache não encontrado. Iniciando novo cache.")

carregar_proxies_cache()

def scrape_proxies(url):
    try:
        logger.info(f"Scraping proxies from {url}")
        response = requests.get(url, timeout=30)
        proxies = response.text.splitlines()
        return [proxy for proxy in proxies if re.match(IP_PORT_PATTERN, proxy)]
    except requests.exceptions.RequestException as e:
        logger.error(f"Error accessing {url}: {e}")
        return []

def process_proxy_list(urls, category):
    all_proxies = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(scrape_proxies, urls)
        for proxies in results:
            all_proxies.extend(proxies)
    return category, list(set(all_proxies))

def paginate_proxies(proxies, page):
    start = (page - 1) * LINES_PER_PAGE
    end = start + LINES_PER_PAGE
    return proxies[start:end]

async def check_proxy(proxy, session):
    try:
        start_time = time.time()  # Marca o início da verificação
        logger.info(f"Checking proxy: {proxy}")
        async with session.get("http://httpbin.org/ip", proxy=f"http://{proxy}", timeout=100) as response:
            if response.status == 200:
                end_time = time.time()  # Marca o fim da verificação
                latencia = end_time - start_time  # Calcula a latência
                logger.info(f"Proxy {proxy} is working with latency {latencia}")
                return proxy, latencia
    except Exception as e:
        logger.error(f"Error checking proxy {proxy}: {e}")
    return None, None

async def check_proxies(proxies):
    async with ClientSession() as session:
        tasks = [check_proxy(proxy, session) for proxy in proxies]
        results = await asyncio.gather(*tasks)
        return {proxy: latencia for proxy, latencia in results if proxy}

def atualizar_cache_proxies():
    global proxies_cache, ultima_atualizacao
    try:
        logger.info("Iniciando a checagem de proxies.")
        categories = ['http', 'socks4', 'socks5']
        for category in categories:
            urls = globals()[f'{category}_urls']
            cat, proxies = process_proxy_list(urls, category)
            proxies_para_verificar = [proxy for proxy in proxies if proxy not in proxies_cache[cat]]

            proxy_results = asyncio.run(check_proxies(proxies_para_verificar))

            for proxy, latency in proxy_results.items():
                if latency is not None and proxy not in proxies_cache[cat]:  # Verifica se o proxy não está no cache
                    proxies_cache[cat][proxy] = {
                        'ultima_verificacao': datetime.datetime.now(),
                        'latencia': latency,
                    }

        ultima_atualizacao = datetime.datetime.now()

        logger.info("Checagem de proxies concluída e cache atualizado.")
    except Exception as e:
        logger.error(f"Erro durante a checagem de proxies: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(atualizar_cache_proxies, 'interval', hours=1)
    
# Substitua com os URLs dos seus proxies
http_urls = [
    "https://api.proxyscrape.com/?request=getproxies&proxytype=https&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/saisuiu/Lionkings-Http-Proxys-Proxies/main/cnfree.txt",
    "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/http_proxies.txt",
    "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/https_proxies.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/https/https.txt",
    "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/http/http.txt"
]
socks4_urls = [
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks4",
    "https://api.proxyscrape.com/?request=displayproxies&proxytype=socks4&country=all",
    "https://api.openproxylist.xyz/socks4.txt",
    "https://proxyspace.pro/socks4.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/socks4.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4_RAW.txt",
    "https://proxyspace.pro/socks4.txt",
    "https://www.proxy-list.download/api/v1/get?type=socks4",
    "https://raw.githubusercontent.com/HyperBeats/proxy-list/main/socks4.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt",
    "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks4.txt",
    "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/SOCKS4.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies_anonymous/socks4.txt",
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks4.txt",
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks4.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks4.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/socks4.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/socks4.txt",
    "https://raw.githubusercontent.com/elliottophellia/yakumo/master/results/socks4/global/socks4_checked.txt",
    "https://raw.githubusercontent.com/zloi-user/hideip.me/main/socks4.txt",
    "https://proxylist.geonode.com/api/proxy-list?protocols=socks4&speed=fast&google=false&limit=500&sort_by=lastChecked&sort_type=desc"
]
socks5_urls = [
    "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/SOCKS5.txt",
    "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks5.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
    "https://raw.githubusercontent.com/HyperBeats/proxy-list/main/socks5.txt",
    "https://api.openproxylist.xyz/socks5.txt",
    "https://api.proxyscrape.com/?request=displayproxies&proxytype=socks5",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5",
    "https://proxyspace.pro/socks5.txt",
    "https://raw.githubusercontent.com/manuGMG/proxy-365/main/SOCKS5.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/socks5.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies_anonymous/socks5.txt",
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks5.txt",
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks5.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks5.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/socks5.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/socks5.txt",
    "https://raw.githubusercontent.com/elliottophellia/yakumo/master/results/socks4/global/socks5_checked.txt",
    "https://spys.me/socks.txt",
    "https://raw.githubusercontent.com/zloi-user/hideip.me/main/socks5.txt",
    "https://proxylist.geonode.com/api/proxy-list?protocols=socks5&speed=fast&google=false&limit=500&sort_by=lastChecked&sort_type=desc"
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<string:category>/<int:page>')
def categorized_proxies(category, page):
    if category in proxies_cache:
        page_proxies = paginate_proxies(list(proxies_cache[category].keys()), page)
        return Response('\n'.join(page_proxies), mimetype='text/plain')
    else:
        return Response(f"Categoria inválida: {category}", status=400)
    
@app.route('/stats')
def proxy_stats():
    tempo_atual = datetime.datetime.now()
    tempo_para_proxima_atualizacao = (ultima_atualizacao + datetime.timedelta(hours=1)) - tempo_atual
    segundos_para_proxima_atualizacao = int(tempo_para_proxima_atualizacao.total_seconds())
    
    stats = {
        'http': len(proxies_cache['http']),
        'socks4': len(proxies_cache['socks4']),
        'socks5': len(proxies_cache['socks5']),
        'next_update': segundos_para_proxima_atualizacao
    }
    return jsonify(stats)


if __name__ == '__main__':
    atualizar_cache_proxies()
    scheduler.start()
    app.run(debug=True)