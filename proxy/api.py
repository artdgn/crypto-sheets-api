import logging
from typing import Union, List, Dict

import fastapi
import jsonpath_ng
import requests
import xmltodict
from starlette import responses

logger = logging.getLogger(__name__)

app = fastapi.FastAPI(title='Cryptocurrency data API for Google Sheets')

ROOT_KEY = 'result'
COINGECKO_ADDRESS = 'https://api.coingecko.com/api/v3/'

@app.get('/', response_class=responses.HTMLResponse)
def health():
    """Just a welcome text"""
    return """
        Welcome!<br>
        <a href="/docs">Docs UI</a>?<br>
        <a href="https://github.com/artdgn/crypto-sheets-api" target="_blank">GitHub</a>?
        """


@app.get("/xml/coingecko/{route:path}", response_class=responses.PlainTextResponse)
def get_xml_coingecko(route: str, _request: fastapi.Request, jsonpath: str = None) -> str:
    """
    GET JSON data from any route of the CoinGecko API and encode it as XML, optionally extracting
    parts from it using [JSONPath](https://goessner.net/articles/JsonPath/).

    > Use [CoinGecko API live docs](https://www.coingecko.com/ja/api#explore-api)
    to create your route and parameters.

    ### Parameters:
    - route: CoinGecko API route (e.g. `simple/price`, or `coins/bitcoin`)
    - jsonpath: optional [jsonpath](https://goessner.net/articles/JsonPath/)
        to apply to resulting JSON before encoding as XML
        in case full JSON is not a valid XML (or just to simplify xpath expression)

    ### Returns:
    JSON response encoded as XML under the root "result" field.

    ### Example usage in Sheets:
    ```
    =importxml("https://your-api-address/xml/coingecko/simple/price?
        ids=bitcoin&vs_currencies=usd", "result/bitcoin/usd")
    ```

    Same example but using JSONPath expression:
    ```
    =importxml("https://your-api-address/xml/coingecko/simple/price?
        ids=bitcoin&vs_currencies=usd&jsonpath=bitcoin.usd", "result")
    ```
    """
    return _get_request_to_xml(
        url=f'{COINGECKO_ADDRESS}{route}',
        params=_upcaptured_query_params(_request, ['jsonpath']),
        jsonpath=jsonpath)


@app.get("/xml/any/{url:path}", response_class=responses.PlainTextResponse)
def get_xml_any(url: str, _request: fastapi.Request, jsonpath: str = None) -> str:
    """
    GET any JSON from any API and encode it as XML, optionally extracting
    parts from it using [JSONPath](https://goessner.net/articles/JsonPath/).

    ### Parameters:
    - url: url path with parameters already encoded
    - jsonpath: optional [jsonpath](https://goessner.net/articles/JsonPath/)
        to apply to resulting JSON before encoding as XML
        in case full JSON is not a valid XML (or just to simplify xpath expression)

    ### Returns:
    JSON response encoded as XML under the root "result" field.

    ### Example usage in Sheets:
    - Usage in sheets if you want to query the Chuck Norris jokes API
        for a random dirty joke and get the joke value using an XPath expression:
    ```
    =importxml("https://your-api-address/xml/any/
            https://api.icndb.com/jokes/random?limitTo=[explicit]",
            "result/value/joke")
    ```

    - Same example but using JSONPath expression:
    ```
    =importxml("https://your-api-address/xml/any/
            https://api.icndb.com/jokes/random?limitTo=[explicit]&jsonpath=value.joke",
            "result")
    ```
    """
    return _get_request_to_xml(
        url=url,
        params=_upcaptured_query_params(_request, ['url', 'jsonpath']),
        jsonpath=jsonpath)


@app.get("/value/coingecko/{route:path}", response_class=responses.PlainTextResponse)
def get_value_coingecko(route: str, jsonpath: str, _request: fastapi.Request) -> str:
    """
    GET any value from any route of the CoinGecko API by extracting it
    using [JSONPath](https://goessner.net/articles/JsonPath/).
    This allows using [IMPORTDATA](https://support.google.com/docs/answer/3093335)
    in Sheets.

    > Warning: IMPORTDATA is
    [limited to 50 calls per sheet](https://support.google.com/docs/answer/3093335)

    ### Parameters:
    - jsonpath: [jsonpath](https://goessner.net/articles/JsonPath/)
        to extract the value from the returned JSON

    ### Returns:
    Value returned as plain text

    ### Example usage in Sheets:
    ```
    =importdata("https://your-api-address/value/coingecko/simple/price?
        ids=bitcoin&vs_currencies=usd&jsonpath=bitcoin.usd")
    ```

    """
    return _get_request_to_value(
        url=f'{COINGECKO_ADDRESS}{route}',
        params=_upcaptured_query_params(_request, ['jsonpath']),
        jsonpath=jsonpath,
    )


@app.get("/value/any/{url:path}", response_class=responses.PlainTextResponse)
def get_value_any(url: str, jsonpath: str, _request: fastapi.Request) -> str:
    """
    GET any value from any API returning a JSON by extracting the
    value using [JSONPath](https://goessner.net/articles/JsonPath/).
    This allows using [IMPORTDATA](https://support.google.com/docs/answer/3093335)
    in Sheets.

    > Warning: IMPORTDATA is
    [limited to 50 calls per sheet](https://support.google.com/docs/answer/3093335)

    ### Parameters:
    - url: url path with parameters already encoded
    - jsonpath: [jsonpath](https://goessner.net/articles/JsonPath/)
        to extract the value from the returned JSON

    ### Returns:
    Value returned as plain text

    ### Example usage in Sheets:
    - Usage in sheets if you want to query the Chuck Norris jokes API
        for a random dirty joke:
    ```
    =importdata("https://your-api-address/value/any/
                https://api.icndb.com/jokes/random?limitTo=[explicit]
                &jsonpath=value.joke")
    ```

    """
    return _get_request_to_value(
        url=url,
        params=_upcaptured_query_params(_request, ['url', 'jsonpath']),
        jsonpath=jsonpath,
    )


def _upcaptured_query_params(request: fastapi.Request, expected_args: List[str]
                             ) -> dict:
    """
    Extract any query params that are not captured because of `&` splitting.
    """
    return {k: v for k, v in request.query_params.items()
            if k not in expected_args}


def _get_request_to_xml(url: str, params: dict, jsonpath: str = None) -> str:
    """ send a get request and convert to XML optionally applying jsonpath"""
    try:
        response = requests.get(url, params=params)
        if not response.ok:
            raise fastapi.HTTPException(response.status_code, response.text)
        result = response.json()
        result = _try_apply_jsonpath(result, jsonpath) if jsonpath else result

    except Exception as e:
        result = f'error: {str(e)}'

    return _to_xml(result)


def _get_request_to_value(url: str, params: dict, jsonpath: str) -> str:
    """ send a get request and extract value using jsonpath"""
    try:
        response = requests.get(url, params=params)
        return _single_value_jsonpath_result(response, jsonpath)

    except Exception as e:
        return f'error: {str(e)}'


def _single_value_jsonpath_result(response: requests.Response, jsonpath: str
                                  ) -> str:
    """
    Checks and extracts a single value from the response according to the jsonpath.
    """
    if not response.ok:
        raise fastapi.HTTPException(response.status_code, response.text)

    result = response.json()

    # jsonpath
    values = [match.value for match in jsonpath_ng.parse(jsonpath).find(result)]

    if not len(values):
        raise ValueError(f'match for {jsonpath} not found')
    if len(values) > 1:
        raise ValueError(f'more than one match for {jsonpath}')

    return str(values[0])


def _try_apply_jsonpath(result: Union[dict, list],
                        jsonpath: str
                        ) -> Union[dict, list]:
    """ Applies jsonpath expression or adds the error that results from trying """
    try:
        values = [match.value for match in jsonpath_ng.parse(jsonpath).find(result)]
        if len(values) == 1:
            result = values[0]
        elif not len(values):
            raise ValueError(f'match for {jsonpath} not found')
        else:
            result = values

    except Exception as e:
        err_info = {'jsonpath-error': str(e)}
        if isinstance(result, dict):
            result.update(err_info)
        else:
            result.append(err_info)
        logger.error(f'jsonpath error: {e}')

    return result


def _to_xml(result: Union[List, Dict]) -> str:
    """
    Wraps a result in a single root structure
    suitable for XML, and converts to XML
    """
    if isinstance(result, list):
        single_root = {ROOT_KEY: {'items': result}}
    else:
        single_root = {ROOT_KEY: result}

    return xmltodict.unparse(single_root, pretty=True)
