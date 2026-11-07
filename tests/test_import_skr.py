import unittest
import tempfile
import json
import zipfile
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from import_skr import extract,read_workbook

class ImportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.file=Path(self.temp.name)/'book.xlsm'
        with zipfile.ZipFile(self.file,'w') as z:
            z.writestr('xl/workbook.xml','<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Revenue" r:id="rId1"/></sheets></workbook>')
            z.writestr('xl/_rels/workbook.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
            z.writestr('xl/worksheets/sheet1.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Motala</t></is></c><c r="B1"><v>2400000</v></c><c r="C1"><f>1+1</f><v>1000000</v></c><c r="D1"><v>43131</v></c><c r="E1"><f>SUM(B1:C1)</f></c></row></sheetData></worksheet>')
            z.writestr('xl/vbaProject.bin',b'Unexecuted macro data')
        self.mapping={'vintage':'2026-10-06','populationReference':'1 November previous year','municipalityCheck':{'sheet':'Revenue','cell':'A1','expected':'Motala'},'rows':[{'year':2026,'tax':{'sheet':'Revenue','cell':'B1','scale':0.001},'grants':{'sheet':'Revenue','cell':'C1','scale':0.001},'population':{'sheet':'Revenue','cell':'D1'}}]}
    def tearDown(self): self.temp.cleanup()
    def set_municipality_cell(self,xml):
        with zipfile.ZipFile(self.file) as source:
            files={name:source.read(name) for name in source.namelist()}
        name='xl/worksheets/sheet1.xml'
        start=files[name].index(b'<c r="A1"')
        end=files[name].index(b'</c>',start)+len(b'</c>')
        files[name]=files[name][:start]+xml.encode()+files[name][end:]
        with zipfile.ZipFile(self.file,'w') as destination:
            for name,content in files.items(): destination.writestr(name,content)
    def test_conversion_provenance_and_formula_cache(self):
        out=extract(self.file,self.mapping)
        self.assertEqual(out['rows'][0],{'year':2026,'tax':2400,'grants':1000,'population':43131})
        self.assertEqual(len(out['provenance']['sha256']),64)
        self.assertTrue(out['provenance']['cachedFormulasNotRecalculated'])
        self.assertEqual(read_workbook(self.file)['Revenue']['C1']['formula'],'1+1')
    def test_calculated_municipality_cell_must_be_recalculated_motala(self):
        # C1 is a formula whose cached value (1000000) does not name Motala: an unrecalculated workbook.
        self.mapping['calculatedMunicipalityCheck']={'sheet':'Revenue','cell':'C1'}
        with self.assertRaisesRegex(ValueError,'not recalculated'): extract(self.file,self.mapping)
        # A1 names Motala but is plain input, so it cannot prove a recalculation.
        self.mapping['calculatedMunicipalityCheck']={'sheet':'Revenue','cell':'A1'}
        with self.assertRaisesRegex(ValueError,'formula cell'): extract(self.file,self.mapping)
        self.set_municipality_cell('<c r="A1" t="str"><f>"Motala"</f><v>Motala</v></c>')
        self.assertTrue(extract(self.file,self.mapping)['provenance']['calculatedMunicipalityVerified'])
    def test_wrong_municipality_is_rejected(self):
        self.mapping['municipalityCheck']['expected']='Stockholm'
        with self.assertRaisesRegex(ValueError,'Municipality'): extract(self.file,self.mapping)
    def test_other_municipality_cannot_be_relabelled_by_matching_mapping(self):
        self.set_municipality_cell('<c r="A1" t="inlineStr"><is><t>Stockholm</t></is></c>')
        self.mapping['municipalityCheck']['expected']='Stockholm'
        with self.assertRaisesRegex(ValueError,'Municipality'): extract(self.file,self.mapping)
    def test_actual_municipality_must_be_motala(self):
        self.set_municipality_cell('<c r="A1" t="inlineStr"><is><t>Stockholm</t></is></c>')
        with self.assertRaisesRegex(ValueError,'Municipality selection'): extract(self.file,self.mapping)
    def test_motala_name_and_text_codes_are_supported(self):
        for value in ('Motala',' MOTALA ','0583','583','583.0'):
            with self.subTest(value=value):
                self.set_municipality_cell(f'<c r="A1" t="inlineStr"><is><t>{value}</t></is></c>')
                self.mapping['municipalityCheck']['expected']=value
                self.assertEqual(extract(self.file,self.mapping)['municipality'],'0583')
    def test_excel_numeric_municipality_code_matches_zero_padded_mapping(self):
        self.set_municipality_cell('<c r="A1"><v>583</v></c>')
        self.mapping['municipalityCheck']['expected']='0583'
        self.assertEqual(extract(self.file,self.mapping)['municipality'],'0583')
    def test_wrong_numeric_municipality_code_is_rejected(self):
        self.set_municipality_cell('<c r="A1"><v>180</v></c>')
        for expected in ('0583',180):
            with self.subTest(expected=expected):
                self.mapping['municipalityCheck']['expected']=expected
                with self.assertRaisesRegex(ValueError,'Municipality'): extract(self.file,self.mapping)
    def test_missing_formula_cache_is_rejected(self):
        self.mapping['rows'][0]['tax']['cell']='E1'
        with self.assertRaisesRegex(ValueError,'No cached value'): extract(self.file,self.mapping)

if __name__=='__main__': unittest.main()
