import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError
from motala_lab import data,import_csv,public_data


class InputTests(unittest.TestCase):
    def mapping(self):
        return {'scope':'kommunen','moneyUnit':'mnkr','definitions':data.DEFINITIONS,
                'evidenceClass':'retrospective','columns':{k:k for k in ('municipality','year',*data.METRICS)},
                'source':'synthetic CSV','vintage':'test','retrievedAt':'2026-10-13','sourceRelease':None}

    def test_reviewed_csv_retains_codes_and_signed_finance(self):
        text='municipality,year,taxAndGrants,netCost,financeNet,result,population\n583,2021,100,90,-2,8,1000\n'
        r=import_csv.convert(text,self.mapping())['rows'][0]
        self.assertEqual(r['municipality'],'0583');self.assertEqual(r['financeNet'],-2)

    def test_missing_values_and_benchmark_inputs_are_rejected(self):
        text='municipality,year,taxAndGrants,netCost,financeNet,result,population\n583,2021,100,90,,8,1000\n'
        with self.assertRaises(ValueError):import_csv.convert(text,self.mapping())
        mapping=self.mapping();mapping['role']='benchmark_only'
        with self.assertRaises(ValueError):import_csv.convert(text,mapping)

    def test_network_failure_is_recorded_without_fake_data(self):
        sources=[{'id':'one','url':'https://example.invalid/a','format':'json'},
                 {'id':'two','url':'https://example.invalid/b','format':'json'}]
        with tempfile.TemporaryDirectory() as directory,patch('motala_lab.public_data.urlopen',side_effect=URLError('DNS failed')) as call:
            receipts=public_data.acquire(directory,sources)
            self.assertEqual(call.call_count,1)
            self.assertEqual([r['status'] for r in receipts],['failed','not_attempted'])
            self.assertTrue(all('sha256' not in r for r in receipts))

    def test_success_is_hashed_but_not_called_normalized(self):
        response=io.BytesIO(b'{"values":[],"next":"page2"}');response.url='https://example.invalid/data'
        with tempfile.TemporaryDirectory() as directory,patch('motala_lab.public_data.urlopen',return_value=response):
            receipt=public_data.acquire(directory,[{'id':'one','url':response.url,'format':'json'}])[0]
            self.assertEqual(receipt['status'],'downloaded')
            self.assertTrue((Path(directory)/receipt['path']).exists())
            self.assertEqual(receipt['normalizationStatus'],'pending_definition_review')
            self.assertTrue(receipt['requiresPaginationReview'])
