# Proxy Checker

Este é um aplicativo simples em Python desenvolvido com Flask para verificar a disponibilidade e a latência de proxies HTTP, SOCKS4 e SOCKS5.

## Funcionalidades

- Scraping de proxies de várias fontes online.
- Verificação de proxies utilizando asyncio e aiohttp.
- Atualização automática do cache de proxies em segundo plano utilizando o APScheduler.

## Instalação

1. Clone este repositório:

```
git clone github.com:msouza10/proxyscrape_api.git
cd proxyscrape_api
```

2. Instale as dependências:

```
pip install -r requirements.txt
```

## Utilização

1. Execute o aplicativo:

```
python app.py
```

2. Acesse o aplicativo em seu navegador no endereço [http://localhost:5000](http://localhost:5000).

## Rotas

- `/`: Página inicial do aplicativo.
- `/<categoria>/<página>`: Lista de proxies paginada por categoria (http, socks4, socks5).
- `/stats`: Estatísticas sobre o cache de proxies, incluindo o número de proxies em cada categoria e o tempo restante para a próxima atualização.

## Configuração

- As URLs dos proxies são definidas nas listas `http_urls`, `socks4_urls` e `socks5_urls` no arquivo `app.py`. Você pode adicionar ou remover URLs conforme necessário.
- O intervalo de atualização do cache de proxies pode ser configurado no scheduler (`BackgroundScheduler`) no arquivo `app.py`.

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir uma issue ou enviar um pull request.

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).
