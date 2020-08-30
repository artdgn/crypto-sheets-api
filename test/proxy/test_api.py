import pytest
import xmltodict
from fastapi import testclient

from proxy import api


XML_ROOT = api.ROOT_KEY

@pytest.fixture(scope='module')
def api_client():
    return testclient.TestClient(api.app)


@pytest.mark.integration
def test_health(api_client):
    res = api_client.get('/')
    assert res.ok
    assert '/docs' in res.text

@pytest.mark.integration
class TestCoingeckoXMLAny:
    route = '/xml/coingecko'

    def test_basic_and_jsonpath(self, api_client):
        ids = ['bitcoin', 'ethereum']
        currencies = ['usd', 'aud']
        params = {
            'ids': ','.join(ids),
            'vs_currencies': ','.join(currencies),
        }
        res = api_client.get(f'{self.route}/simple/price', params=params)
        assert res.ok
        data = xmltodict.parse(res.text)
        assert set(data[XML_ROOT].keys()) == set(ids)
        assert set(data[XML_ROOT][ids[0]]) == set(currencies)

        # check jsonpath works
        res_jsonpath = api_client.get(
            f'{self.route}/simple/price',
            params=dict(**params, jsonpath=f'{ids[1]}.{currencies[1]}'))
        data_jsonpath = xmltodict.parse(res_jsonpath.text)
        assert data_jsonpath[XML_ROOT] == data[XML_ROOT][ids[1]][currencies[1]]


@pytest.mark.integration
class TestCoingeckoValueAny:
    route = '/value/coingecko'

    def test_basic_and_jsonpath(self, api_client):
        ids = ['bitcoin', 'ethereum']
        currencies = ['usd', 'aud']
        params = {
            'ids': ','.join(ids),
            'vs_currencies': ','.join(currencies),
        }
        # use XML endpoint result for reference
        res_xml = api_client.get(f'{TestCoingeckoXMLAny.route}/simple/price', params=params)
        xml_data = xmltodict.parse(res_xml.text)

        # test value result vs the xml result
        res_value = api_client.get(
            f'{self.route}/simple/price',
            params=dict(**params, jsonpath=f'{ids[1]}.{currencies[1]}'))
        assert res_value.text == xml_data[XML_ROOT][ids[1]][currencies[1]]


@pytest.mark.integration
class TestXMLGetJSON:
    route = '/xml/any'

    def test_basic(self, api_client):
        url = 'https://api.icndb.com/jokes/random'
        res = api_client.get(f'{self.route}/{url}')
        assert res.ok
        data = xmltodict.parse(res.text)

        # test may be flaky, Chuck Norris doesn't have to be
        # part of a Chuck Norris joke if he doesn't feel like it
        assert 'chuck' in data[XML_ROOT]['value']['joke'].lower()

    @pytest.mark.parametrize('url', [
        'https://jsonplaceholder.typicode.com/',  # url not returning a JSON
        'https://anskjvas/'  # HTTP error
    ])
    def test_json_errors(self, api_client, url):
        res = api_client.get(f'{self.route}/{url}')
        assert res.ok
        data = xmltodict.parse(res.text)
        assert 'error' in data[XML_ROOT]

    def test_multiple_params(self, api_client):
        url = ('https://api.coingecko.com/api/v3/simple/price?'
               'ids=bitcoin&vs_currencies=aud')
        res = api_client.get(f'{self.route}/{url}')
        data = xmltodict.parse(res.text)
        # vs_currencies parameter was not ignored
        assert data[XML_ROOT]['bitcoin']['aud']

    def test_jsonpath(self, api_client):
        url = 'https://jsonplaceholder.typicode.com/posts/1/comments'
        res = api_client.get(f'{self.route}/{url}',
                             params=dict(jsonpath='[1].email'))
        data = xmltodict.parse(res.text)
        assert '@' in data[XML_ROOT].lower()

    @pytest.mark.parametrize('url', [
        'https://jsonplaceholder.typicode.com/posts/1',
        'https://jsonplaceholder.typicode.com/posts/1/comments',
    ])
    @pytest.mark.parametrize('jsonpath', [
        '/#$',
        '[10].email'
    ])
    def test_jsonpath_errors(self, api_client, url, jsonpath):
        res = api_client.get(f'{self.route}/{url}',
                             params=dict(jsonpath=jsonpath))
        data = xmltodict.parse(res.text)
        assert data
        assert 'jsonpath-error' in res.text


@pytest.mark.integration
class TestValueGet:
    route = '/value/any'

    def test_basic_jsonpath(self, api_client):
        url = 'https://jsonplaceholder.typicode.com/posts/1/comments'
        res = api_client.get(f'{self.route}/{url}',
                             params=dict(jsonpath='[1].email'))
        assert '@' in res.text

    @pytest.mark.parametrize('jsonpath, error_text', [
        ('/#$', 'Unexpected character'),
        ('[10].email', 'not found'),
        ('[*].email', 'more than one'),
    ])
    def test_jsonpath_errors(self, api_client, jsonpath, error_text):
        url = 'https://jsonplaceholder.typicode.com/posts/1/comments'
        res = api_client.get(f'{self.route}/{url}',
                             params=dict(jsonpath=jsonpath))
        assert 'error' in res.text and error_text in res.text
