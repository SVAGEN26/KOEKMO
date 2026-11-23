"""The local MCP server over stdio and HTTP. Simulation tests need OpenModelica and are skipped without it."""
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / 'scripts' / 'mcp_server.py'
OMC = os.environ.get('OMC') or shutil.which('omc')


class Stdio:
    def __init__(self):
        self.process = subprocess.Popen([sys.executable, str(SERVER)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL, text=True, cwd=ROOT)
        self.next_id = 0

    def request(self, method, params=None):
        self.next_id += 1
        self.process.stdin.write(json.dumps({'jsonrpc': '2.0', 'id': self.next_id, 'method': method, 'params': params or {}}) + '\n')
        self.process.stdin.flush()
        return json.loads(self.process.stdout.readline())

    def tool(self, name, **arguments):
        result = self.request('tools/call', {'name': name, 'arguments': arguments})['result']
        return result.get('structuredContent'), result['isError'], result['content'][0]['text']

    def close(self):
        self.process.stdin.close()
        self.process.wait(timeout=10)
        self.process.stdout.close()


class Protocol(unittest.TestCase):
    def setUp(self):
        self.server = Stdio()

    def tearDown(self):
        self.server.close()

    def test_initialize_and_list(self):
        init = self.server.request('initialize', {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 'test', 'version': '0'}})
        self.assertEqual(init['result']['protocolVersion'], '2025-06-18')
        self.assertIn('tools', init['result']['capabilities'])
        names = [t['name'] for t in self.server.request('tools/list')['result']['tools']]
        for name in ('start_session', 'set_decisions', 'advance', 'save_session'):
            self.assertIn(name, names)
        self.assertIn('budget_round', [p['name'] for p in self.server.request('prompts/list')['result']['prompts']])

    def test_catalogue_and_municipalities(self):
        data, error, _ = self.server.tool('list_municipalities')
        self.assertFalse(error)
        codes = {m['code'] for m in data['municipalities']}
        self.assertEqual(len(codes), 13)
        self.assertIn('0583', codes)
        data, _, _ = self.server.tool('list_parameters', all=True)
        shapes = {p['name']: p['shape'] for p in data['parameters']}
        self.assertEqual(shapes['investmentPath'], 'perYear')
        self.assertEqual(shapes['taxRatePath'], 'perYear')
        self.assertEqual(shapes['residualMigrationPath'], 'perYearGroups')
        self.assertNotIn('base', shapes)

    def test_reference_is_cited(self):
        data, _, _ = self.server.tool('reference', municipality='0562')
        self.assertEqual(data['skr']['source']['circular'], '26:28')
        self.assertIn('2025', data['accounts'])

    def test_unknown_method(self):
        self.assertEqual(self.server.request('nothing')['error']['code'], -32601)


@unittest.skipUnless(OMC, 'OpenModelica not available')
class Session(unittest.TestCase):
    def test_year_by_year(self):
        server = Stdio()
        try:
            data, error, text = server.tool('start_session', municipality='0583', model='Continuous', horizon=3)
            self.assertFalse(error, text)
            session = data['session']
            self.assertEqual(data['accounts']['result'], 104.0)
            _, error, text = server.tool('set_decisions', session=session, year=2026,
                                         values={'investmentPath': 300, 'taxRatePath': 22.2}, reason='test')
            self.assertFalse(error, text)
            data, error, text = server.tool('advance', session=session)
            self.assertFalse(error, text)
            year = data['years'][0]
            self.assertEqual(year['year'], 2026)
            self.assertAlmostEqual(year['annualInvestment'], 300, places=6)
            self.assertTrue(year['checksOk'])
            self.assertIn('skr', year)
            # the past is fixed; client text never reaches the compiler
            _, error, text = server.tool('set_decisions', session=session, year=2026, values={'investmentPath': 200})
            self.assertTrue(error)
            _, error, text = server.tool('set_decisions', session=session, year=2027, values={'investmentPath': '1); x = (2'})
            self.assertTrue(error)
            # a higher tax rate from 2027 raises 2027's tax against the default run
            server.tool('set_decisions', session=session, year=2027, values={'taxRatePath': 23.0})
            data, _, _ = server.tool('advance', session=session)
            plain, _, _ = server.tool('run_scenario', municipality='0583', model='Continuous', horizon=3,
                                      values={'investmentPath': [300, 413, 413]})
            self.assertGreater(data['years'][0]['tax'], plain['years'][2]['tax'] + 50)
        finally:
            server.close()

    def test_higher_interest_passes_through_gradually(self):
        server = Stdio()
        try:
            base, _, _ = server.tool('run_scenario', municipality='0583', horizon=3)
            high, error, text = server.tool('run_scenario', municipality='0583', horizon=3, scenario='higherInterest')
            self.assertFalse(error, text)
            rates = [y['annualInterestRate'] for y in high['years'][1:]]
            self.assertEqual(rates, sorted(rates))  # the average rate climbs year by year
            first, plain = high['years'][1], base['years'][1]
            full = plain['annualInterestRate'] + 0.03
            self.assertGreater(first['annualInterestRate'], plain['annualInterestRate'] + 0.005)
            self.assertLess(first['annualInterestRate'], full - 0.01)  # 3.19 years of fixed rates: not all at once
            self.assertLess(first['result'], plain['result'])
        finally:
            server.close()

    def test_higher_inflation_hits_costs_before_tax(self):
        server = Stdio()
        try:
            base, _, _ = server.tool('run_scenario', municipality='0583', horizon=3)
            high, error, text = server.tool('run_scenario', municipality='0583', horizon=3, scenario='higherInflation')
            self.assertFalse(error, text)
            b1, h1, b2, h2 = base['years'][1], high['years'][1], base['years'][2], high['years'][2]
            self.assertAlmostEqual(h1['tax'], b1['tax'], places=6)  # the tax base follows wages a year later
            self.assertGreater(h2['tax'], b2['tax'])
            self.assertGreater(h1['otherOperatingExpense'], b1['otherOperatingExpense'])
            self.assertAlmostEqual(h1['grants'], b1['grants'], places=6)  # fixed in kronor without compensation
            self.assertLess(h1['result'], b1['result'])
            self.assertGreater(h1['annualInterestRate'], b1['annualInterestRate'])
        finally:
            server.close()


class Http(unittest.TestCase):
    def test_post_and_origin(self):
        with socket.socket() as s:
            s.bind(('127.0.0.1', 0))
            port = s.getsockname()[1]
        process = subprocess.Popen([sys.executable, str(SERVER), '--http', str(port)], stderr=subprocess.DEVNULL, cwd=ROOT)
        try:
            url = f'http://127.0.0.1:{port}/mcp'
            body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-03-26'}}).encode()
            for _ in range(50):
                try:
                    response = urllib.request.urlopen(urllib.request.Request(url, body, {'Content-Type': 'application/json'}))
                    break
                except urllib.error.URLError:
                    time.sleep(0.1)
            self.assertEqual(json.loads(response.read())['result']['protocolVersion'], '2025-03-26')
            self.assertTrue(response.headers['Mcp-Session-Id'])
            foreign = urllib.request.Request(url, body, {'Content-Type': 'application/json', 'Origin': 'https://example.com'})
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(foreign)
            self.assertEqual(caught.exception.code, 403)
        finally:
            process.terminate()
            process.wait(timeout=10)


if __name__ == '__main__':
    unittest.main()
