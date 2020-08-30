![CI](https://github.com/artdgn/crypto-sheets-api/workflows/CI/badge.svg) ![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/artdgn/crypto-sheets-api?label=dockerhub&logo=docker) ![GitHub deployments](https://img.shields.io/github/deployments/artdgn/crypto-sheets-api/crypto-sheets-api?label=heroku&logo=heroku)


# Cryptocurrency data API for Google Sheets  
Using CoinGecko API in Sheets to get cryptocurrency price data.

## Basic usage

Use [ImportXML](https://support.google.com/docs/answer/3093342?hl=en) to 
get basic price data:
> `=ImportXML("https://your-api-address/coingecko/xml/price/btc","result")`.
 
![](https://artdgn.github.io/images/crypto-sheets-api.gif)

For full documentation of proxy endpoints (live OpenAPI) go to `https://your-api-address/docs`

## Live example API and Sheet:
- [Example API on Heroku](https://crypto-sheets-api.herokuapp.com) free tier, welcome to use as example. Use "Deploy to Heroku" button below to deploy your own.
- [Example Sheet](https://docs.google.com/spreadsheets/d/1cY8n9s1QnW7HQuMdJjihjpKlVSit2kRAT7oe7lFySLg/edit?usp=sharing) with the examples from this readme.

## Advanced usage for CoingGecko routes
Use `/xml/coingecko` or `/value/coingecko` to import data from any CoinGecko API route.

Use any route on [CoinGecko API live docs](https://www.coingecko.com/ja/api#explore-api) to create your target path.

> Example: Use `/simple/price` to get current bitcoin price in usd: `/simple/price?ids=bitcoin&vs_currencies=usd`. See the options below for usage in Sheets.

### Using ImportXML in Sheets: 
> `=ImportXML("https://your-api-address/xml/coingecko/simple/price?ids=bitcoin&vs_currencies=usd","result/bitcoin/usd")`
<details><summary> Detailed instruction </summary>

> Xpath expression can be used more easilty since the full XML is directly visible as output of the proxy API.

1. Check the proxy API's output XML by going to the proxy URL (e.g. `https://your-api-address/xml/coingecko/simple/price?ids=bitcoin&vs_currencies=usd` in the browser)
2. Use [XPath syntax](https://www.w3schools.com/xml/xpath_syntax.asp) to create an XPath expression to extract your data (example: `result/bitcoin/usd`)

</details>


### Using ImportXML in Sheets with JSONPath: 
> `=ImportXML("https://your-api-address/xml/coingecko/simple/price?ids=bitcoin&vs_currencies=usd&jsonpath=bitcoin.usd","result")`
<details><summary> Detailed instructions</summary>

> JSONPath should be preferred because not every valid JSON can be converted into XML (e.g. if some keys start with numbers).

1. Check CoinGecko's output JSON by going to the target URL in the browser (example: `https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd`).
2. Use [JSONPath syntax](https://restfulapi.net/json-jsonpath/) to create a JSONPath expression to get to your value (example: `bitcoin.usd`).

</details>

### Using ImportDATA in Sheets: 
> `=ImportDATA("https://your-api-address/value/coingecko/simple/price?ids=bitcoin&vs_currencies=usd&jsonpath=bitcoin.usd")`
<details><summary> Detailed instructions</summary>

> ImportDATA is limited to 50 calls per sheet, so should be used in small sheets only.

The `/value/coingecko` endpoint can be used to return just the value as plain text which allows using ImportDATA Sheets function instead of ImportXML.

Follow the same steps as for JSONPath with ImportXML above, but use a `/value/coingecko` proxy route and ImportDATA instead of ImportXML.

</details>

## Usage for any other API (not necessarily CoinGecko)
Use the generic `/xml/any` or `/value/any` to import data from any other API URL that returns a JSON. Intead of CoinGecko routes, use the full target URL. 

For example, in `/xml/coingecko/` example we used:
> `https://your-api-address/xml/coingecko/simple/price?ids=bitcoin&vs_currencies=usd`

The generic equivalent would be: 
> `https://your-api-address/xml/any/https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd` (add `jsonpath` as needed)


## Running the API
For the API to be accessible from Sheets it needs to be publicly accessible 
(because Google is making the requests not from your local machine).

### Host API on Heroku
> This option is best for actual usage (the free tier should be enough). Also best in terms of privacy

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/artdgn/crypto-sheets-api)


### Run API locally and expose publicly via [ngrok](https://ngrok.com/):
> This option is best for development or temporary usage (free as well).

#### 1. Run the API locally:
<details><summary> Local python option </summary>

1. Install in local virtual env after cloning: `make install`
2. Run local server: `make server`

</details>

<details><summary> Docker with local code option </summary>

1. After cloning: `make docker-server`

</details>
    
    
<details><summary> Docker without cloning repo option </summary>

1. `docker run -it --rm -p 9000:9000 artdgn/crypto-sheets-api` (or `-p 1234:9000` to run on different port)

</details>

#### 2. Set up tunnelling: 
<details><summary> Tunnelling with ngrok </summary>

- After [setting up an ngrok account and local client](https://ngrok.com/download):
- Run `/path/to/ngrok http <port-number>` to run ngrok (e.g. `~/ngrok/ngrok http 9000` 
    if ngrok lives in `~/ngrok/` and you're using the default port of 9000. If you have the local 
    repo, you can also just `make ngrok` to run this command.
    
</details>

## Simple manual CLI usage (not API)
<details><summary>Manual CLI usage instructions</summary>

- Copy your column of ticker symbols from sheets.
- Run:
    - Local python virtual environment: `python cli.py "<paste-here>"` (paste before closing the quote)
    - Docker: `docker run -it --rm artdgn/crypto-sheets-api python cli.py "<paste-here>"` 
- Copy paste from terminal output back into sheets. 

</details>


## Alternative solutions
[ImportJSON](https://github.com/bradjasper/ImportJSON) seems to also work, and doesn't require 
any external resources (however, I only found it after similar type of solutions didn't work, and I've already implemented this proxy API).

## Privacy thoughts
<details><summary>Privacy related thoughts</summary>

TL;DR: probably best to host your own.

1. I don't think there's a way to know which accounts are making any of the requests.
2. Hosting your own proxy API (e.g. on Heroku) is probably the best option since your requests will be visible only to your proxy (and Heroku).
3. Hosting a local proxy API via tunnelling (the "ngrok" option) will mean that requests to CoinGecko (or any other API you're using through this) will come from your machine.
4. Using my example deployment means that I can see the request parameters in the logs (but with no idea about the google accounts).

</details>


### Related resources
- I've added a [more generalised version of this](https://github.com/artdgn/sheets-import-json-api) that supports POST requests, and doesn't have crypto-currency related endpoints, or examples. It aims to be useful for any target API, and not specifically for crypto-currency data.