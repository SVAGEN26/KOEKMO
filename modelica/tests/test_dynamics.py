"""Analytic limits, conservation and policy consequences of the continuous model."""
import json
import math
from pathlib import Path
import tempfile
import unittest

from motala_lab import dynamics


class DynamicsInputTests(unittest.TestCase):
    def test_json_overrides_are_data_and_support_matrices(self):
        source = dynamics.scenario_source('base', {'reductionYears': [1, 2, 3],
            'automaticInvestment': True, 'serviceWeights': [[1, 1, 1, 0, 0], [0, 0, 0, 0, 1], [1, 1, 1, 1, 1]]})
        self.assertIn('plant(reductionYears={1,2,3}', source)
        self.assertIn('automaticInvestment=true', source)
        self.assertIn('serviceWeights=[1,1,1,0,0;0,0,0,0,1;1,1,1,1,1]', source)
        for overrides in ([], False, {'x); end Scenario;': 1}, {'wageGrowth': 'system("bad")'}, {'wageGrowth': float('nan')}):
            with self.assertRaises(ValueError):
                dynamics.scenario_source('base', overrides)


class DynamicsManifestTests(unittest.TestCase):
    def test_manifest_uses_inherited_and_explicit_revenue_settings(self):
        with tempfile.TemporaryDirectory(prefix='motala-manifest-tests-') as temp:
            directory = Path(temp)
            parameters = directory / 'parameters.json'
            parameters.write_text(json.dumps({'useExternalRevenue': False, 'useExternalTax': True}))
            for name, flags, extra in (
                ('inherited', (True, False), []),
                ('overridden', (False, True), ['--parameters', str(parameters)]),
            ):
                with self.subTest(name=name):
                    output = directory / name
                    dynamics.main(['--scenario', 'tax-settlement', '--years', '1',
                                   '--output', str(output), *extra])
                    manifest = json.loads((output / 'manifest.json').read_text())
                    resolved = json.loads((output / 'native/resolved-parameters.json').read_text())
                    self.assertEqual((manifest['externalRevenue'], manifest['externalTax']), flags)
                    self.assertIs(manifest['externalRevenue'], resolved['useExternalRevenue']['value'])
                    self.assertIs(manifest['externalTax'], resolved['useExternalTax']['value'])

    def test_missing_or_malformed_runtime_settings_are_not_reported_as_defaults(self):
        with tempfile.TemporaryDirectory(prefix='motala-manifest-inputs-') as temp:
            directory = Path(temp)
            for parameter in ('useExternalRevenue', 'useExternalTax'):
                for entry in (None, {}, {'value': 0}, {'value': 1}, {'value': 'false'}):
                    with self.subTest(parameter=parameter, entry=entry):
                        resolved = {key: {'value': False} for key in ('useExternalRevenue', 'useExternalTax')}
                        if entry is None:
                            del resolved[parameter]
                        else:
                            resolved[parameter] = entry
                        (directory / 'resolved-parameters.json').write_text(json.dumps(resolved))
                        with self.assertRaisesRegex(ValueError, parameter):
                            dynamics.resolved_revenue_modes(directory)


class DynamicsNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='motala-dynamics-tests-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.directory = Path(cls.temp.name)
        source = '''within ;
model Scenario
  MotalaDynamics.Examples.Base base;
  MotalaDynamics.Examples.Base extraReference(plant(interestRate0=0));
  MotalaDynamics.Examples.Base extraDeferred(plant(interestRate0=0,
    extraCostPath={0,50,0},extraCostPaymentPath={0,0,50}));
  MotalaDynamics.Examples.Base extraPaid(plant(interestRate0=0,extraCostPath={0,50}));
  MotalaDynamics.Examples.Base extraPrepaid(plant(interestRate0=0,
    extraCostPath={0,0,50},extraCostPaymentPath={0,50,0}));
  MotalaDynamics.Examples.Base legacy(plant(annualFlowAnchoring=false));
  MotalaDynamics.Examples.Base anchored(plant(demographyEnabled=false,allowClosure=false,
    physicalLifeYears=fill(1e12,3),investment0=0,workInProgress0=0,purchaseCoverage=zeros(3),
    wageGrowth=0.03,priceGrowth=-0.05,taxBaseGrowth=0,grantGrowth=1e-9,feeGrowth=0.02,pensionGrowth=0.1));
  MotalaDynamics.Examples.SchoolDecline slow;
  MotalaDynamics.Examples.FastAdjustment fast;
  MotalaDynamics.Examples.StaffingCut cut;
  MotalaDynamics.Examples.InterestShock rateShock;
  MotalaDynamics.Examples.PensionAccrual pension;
  MotalaDynamics.Examples.Base higherTax(plant(taxRate=0.227));
  MotalaDynamics.Examples.Base automatic(plant(automaticInvestment=true));
  MotalaDynamics.Examples.SupplyConstraint constrained;
  MotalaDynamics.Examples.Base split(plant(payrollShares={0.5,0.3,0.2},
    otherExpenseShares={0.2,0.5,0.3},operatingRevenueShares={0.3,0.1,0.6},
    assetShares={0.6,0.2,0.2},investmentShares={0.1,0.2,0.7}));
  MotalaDynamics.Examples.Base externalRevenue(plant(useExternalRevenue=true,
    externalTax=2500,externalGrants=1000,taxRate=0.227));
  MotalaDynamics.Examples.Base taxReference(plant(useExternalRevenue=true,
    externalTax=2000,externalGrants=1000,interestRate0=0));
  MotalaDynamics.Examples.Base taxDeferred(plant(useExternalRevenue=true,
    externalTax=2000,externalGrants=1000,interestRate0=0,
    externalTaxSettlement=if time>=MotalaDynamics.yearSeconds and time<2*MotalaDynamics.yearSeconds then 50 else 0,
    taxPayments=2000+(if time>=2*MotalaDynamics.yearSeconds and time<3*MotalaDynamics.yearSeconds then 50 else 0)));
  MotalaDynamics.Examples.Base taxRefund(plant(useExternalRevenue=true,
    externalTax=2000,externalGrants=1000,interestRate0=0,
    externalTaxSettlement=if time>=MotalaDynamics.yearSeconds and time<2*MotalaDynamics.yearSeconds then -50 else 0,
    taxPayments=2000+(if time>=2*MotalaDynamics.yearSeconds and time<3*MotalaDynamics.yearSeconds then -50 else 0)));
  MotalaDynamics.Examples.Base taxOpening(plant(useExternalRevenue=true,
    externalTax=2000,externalGrants=1000,interestRate0=0,taxReceivable0=20,
    taxPayments=2000+(if time<MotalaDynamics.yearSeconds then 20 else 0)));
  MotalaDynamics.Examples.Base taxSplit(plant(useExternalRevenue=true,
    externalTax=2000,externalGrants=1000,externalTaxSettlement=-50,taxRate=0.227));
  MotalaDynamics.Examples.SchoolDecline costed(plant(wageGrowth=0,staffReductionCost=fill(0.3,3)));
  MotalaDynamics.Services falling(n=1,staff0={100},staffPerUnit={1},minimumStaff={0},
    hiringYears={1},reductionYears={3},demand={100},capacity={1000},
    staffingTarget={0.8},purchaseCoverage={0},productivity=1);
  MotalaDynamics.Services rising(n=1,staff0={100},staffPerUnit={1},minimumStaff={0},
    hiringYears={1},reductionYears={3},demand={100},capacity={1000},
    staffingTarget={1.2},purchaseCoverage={0},productivity=1);
  MotalaDynamics.Services capped(n=1,staff0={100},staffPerUnit={1},minimumStaff={0},
    hiringYears={1},reductionYears={3},demand={200},capacity={1000},
    staffingTarget={1},purchaseCoverage={1},productivity=1,
    limitStaffChanges=true,maxStaffIncrease={5},maxStaffDecrease={5},
    limitExternalService=true,externalCapacity={10});
  MotalaDynamics.Capital pipeline(n=1,capacity0={100},asset0={1000},units0={0},money0={0},
    physicalLife={1e12},accountingLife={10},constructionYears={2},closureYears={8},planningYears={2},
    allowClosure=false,automaticInvestment=false,desiredCapacity={100},unitCost={10},investmentBudget={20});
  MotalaDynamics.Finance surplus(debt0=1,cash0=81,rate0=0,rateYears=1,
    cashTarget=81,liquidityYears=0.25,repaymentYears=0.25,resultBeforeInterest=100,
    marketRate=0,depreciation=0,disposalLoss=0,pensionExpense=0,pensionPayments=0,investment=0);
end Scenario;
'''
        cls.rows = dynamics.simulate(source, 8, cls.directory / 'combined')

    def plant(self, name):
        prefix = name + '.plant.'
        return [{'time': row['time'], **{key[len(prefix):]: value for key, value in row.items() if key.startswith(prefix)}}
                for row in self.rows]

    def test_opening_accounts_and_bound_inputs_reconcile_to_source(self):
        baseline = json.loads((dynamics.ROOT.parent / 'data/baseline.json').read_text())
        row = self.plant('legacy')[0]
        for key, expected in {'population': sum(baseline['population']), 'tax': baseline['tax'],
                'grants': baseline['grants'], 'payroll': 2288, 'otherOperatingExpense': 1297,
                'operatingRevenue': 751, 'pensionExpense': 190, 'netOperatingCost': 3023,
                'depreciation': 180, 'interest': 21, 'resultRate': 104, 'demography.births': 334,
                'demography.deaths': 468, 'demography.netMigration': -239,
                'workInProgress': baseline['workInProgress']}.items():
            self.assertAlmostEqual(row[key], expected, places=7, msg=key)
        # Reported 105 differs from the rounded ledger; do not silently invent revenue.
        self.assertEqual(baseline['publishedResult'] - row['resultRate'], 1)

    def test_conservation_and_nonnegative_stocks_across_all_policy_scenarios(self):
        for name in ('base', 'extraReference', 'extraDeferred', 'extraPaid', 'extraPrepaid', 'legacy', 'anchored', 'slow', 'fast', 'cut', 'rateShock', 'pension', 'higherTax', 'automatic', 'constrained', 'split', 'externalRevenue', 'costed', 'taxReference', 'taxDeferred', 'taxRefund', 'taxOpening', 'taxSplit'):
            for row in self.plant(name):
                for residual in ('balanceResidual', 'demography.populationResidual', 'finance.cashResidual', 'finance.debtResidual'):
                    self.assertLess(abs(row[residual]), 1e-4, (name, residual))
                for key in ('debt', 'cash', 'assets', 'workInProgress'):
                    self.assertGreaterEqual(row[key], -1e-6)
                self.assertLess(abs(row['finance.borrowing'] * row['finance.repayment']), 1e-7)
                for i in range(1, 4):
                    for key in ('services.staff', 'capital.capacity', 'capital.constructionUnits', 'services.unmetService'):
                        self.assertGreaterEqual(row[f'{key}[{i}]'], -1e-6)
                    self.assertAlmostEqual(row[f'services.delivered[{i}]'] + row[f'services.unmetService[{i}]'],
                                           row[f'demand[{i}]'], places=7)
                    self.assertLessEqual(row[f'capital.investment[{i}]'], row[f'investmentBudget[{i}]'] + 1e-7)

    def test_staff_adjustment_matches_independent_exponential_solutions(self):
        for year in range(1, 9):
            row = dynamics.at_year(self.rows, year)
            self.assertAlmostEqual(row['falling.staff[1]'], 80 + 20 * math.exp(-year / 3), places=4)
            self.assertAlmostEqual(row['rising.staff[1]'], 120 - 20 * math.exp(-year), places=4)

    def test_capped_staffing_has_linear_response_and_unfilled_external_demand(self):
        for year in range(1, 9):
            row = dynamics.at_year(self.rows, year)
            self.assertAlmostEqual(row['capped.staff[1]'], 100 + 5 * year, places=5)
            self.assertAlmostEqual(row['capped.purchasedService[1]'], 10, places=5)
            self.assertAlmostEqual(row['capped.unmetService[1]'], 90 - 5 * year, places=5)
        row = dynamics.at_year(self.plant('constrained'), 2)
        self.assertGreater(row['cumulativeUnmet[2]'], 0)
        limit = 0.05*self.plant('constrained')[0]['demand[2]']
        for row in self.plant('constrained'):
            self.assertLessEqual(row['services.purchasedService[2]'], limit + 1e-7)

    def test_transition_cost_integrates_removed_staff_once(self):
        rows = self.plant('costed')
        for year in range(1, 9):
            row = dynamics.at_year(rows, year)
            removed = sum(rows[0][f'services.staff[{i}]'] - row[f'services.staff[{i}]'] for i in (1, 2, 3))
            self.assertAlmostEqual(row['cumulativeTransitionExpense'], 0.3 * removed, places=5)

    def test_separate_sector_allocations_preserve_opening_totals(self):
        row = self.plant('split')[0]
        wage = 1.03 * math.log1p(0.03) / 0.03
        price = 1.02 * math.log1p(0.02) / 0.02
        for key, expected in {'payroll': 2288*wage, 'otherOperatingExpense': 1297*price,
                              'operatingRevenue': 751*price, 'assets': 2997, 'investment': 413, 'workInProgress': 99}.items():
            self.assertAlmostEqual(row[key], expected, places=6)
        self.assertAlmostEqual(row['payrollByService[1]'], 2288 * 0.5 * wage, places=6)
        self.assertAlmostEqual(row['otherByService[1]'], 1297 * 0.2 * price, places=6)
        self.assertAlmostEqual(row['revenueByService[1]'], 751 * 0.3 * price, places=6)
        self.assertAlmostEqual(row['capital.assets[1]'], 2997 * 0.6, places=6)
        self.assertAlmostEqual(row['capital.investment[1]'], 413 * 0.1, places=6)

    def test_annual_growth_is_growth_of_integrated_totals(self):
        # Independently derived discrete annual totals, not the continuous implementation.
        # Includes negative, zero, near-zero, and positive annual growth.
        for h, row in enumerate(dynamics.annual_rows(self.plant('anchored'), 8, base_year=2010), 1):
            self.assertEqual(row['year'], 2010+h)
            for key, previous, g in [('payroll', 2288, .03), ('otherOperatingExpense', 1297, -.05),
                                     ('tax', 2330, 0), ('grants', 987, 1e-9),
                                     ('operatingRevenue', 751, .02), ('pensionExpense', 190, .1)]:
                self.assertAlmostEqual(row[key], previous*(1+g)**h, delta=2e-4, msg=(key, h))

    def test_external_reference_rate_revenue_bindings(self):
        for row in self.plant('externalRevenue'):
            self.assertAlmostEqual(row['tax'], 2500 * 0.227 / 0.217, places=6)
            self.assertAlmostEqual(row['grants'], 1000, places=6)

    def test_collective_settlement_does_not_scale_with_own_tax_rate(self):
        for row in dynamics.annual_rows(self.plant('taxSplit'), 8):
            self.assertAlmostEqual(row['tax'], 2000*.227/.217-50, delta=2e-4)
            self.assertAlmostEqual(row['taxSettlement'], -50, delta=2e-4)
            self.assertAlmostEqual(row['taxPayments'], row['tax'], delta=2e-4)
            self.assertAlmostEqual(row['taxReceivable'], 0, delta=2e-4)

    def test_tax_receivable_defers_cash_for_income_and_refunds(self):
        reference = dynamics.annual_rows(self.plant('taxReference'), 8)
        for name, sign in (('taxDeferred', 1), ('taxRefund', -1)):
            native = self.plant(name)
            for i, row in enumerate(dynamics.annual_rows(native, 8)):
                booked = sign*50 if i == 1 else 0
                paid = sign*50 if i == 2 else 0
                balance = sign*50 if i == 1 else 0
                self.assertAlmostEqual(row['tax']-reference[i]['tax'], booked, delta=2e-4)
                self.assertAlmostEqual(row['result']-reference[i]['result'], booked, delta=2e-3)
                self.assertAlmostEqual(row['taxPayments']-2000, paid, delta=2e-4)
                self.assertAlmostEqual(row['operatingCash']-reference[i]['operatingCash'], paid, delta=2e-3)
                self.assertAlmostEqual(row['taxReceivable'], balance, delta=2e-4)
                self.assertAlmostEqual(row['balanceResidual'], 0, delta=2e-4)
            # Unpaid recognised income/refund alone cannot finance anything.
            for year in (1, 2):
                before = dynamics.at_year(self.plant('taxReference'), year)
                changed = dynamics.at_year(native, year)
                for stock in ('debt', 'cash'):
                    self.assertAlmostEqual(before[stock], changed[stock], delta=2e-4)

    def test_opening_tax_receivable_collection_is_not_new_income(self):
        reference = dynamics.annual_rows(self.plant('taxReference'), 8)
        native = self.plant('taxOpening')
        self.assertAlmostEqual(native[0]['taxReceivable'], 20, delta=2e-4)
        self.assertAlmostEqual(native[0]['balanceResidual'], 0, delta=2e-4)
        for i, row in enumerate(dynamics.annual_rows(native, 8)):
            self.assertAlmostEqual(row['result'], reference[i]['result'], delta=2e-3)
            self.assertAlmostEqual(row['operatingCash']-reference[i]['operatingCash'],
                                   20 if i == 0 else 0, delta=2e-3)
            self.assertAlmostEqual(row['taxReceivable'], 0, delta=2e-4)
            self.assertAlmostEqual(row['balanceResidual'], 0, delta=2e-4)

    def test_old_native_results_do_not_gain_invented_tax_cash_observations(self):
        keys = set(dynamics.TAX_CASH_COLUMNS.values()) | {'taxReceivable'}
        old = [{k: v for k, v in row.items() if k not in keys} for row in self.plant('base')]
        annual = dynamics.annual_rows(old, 8)
        self.assertNotIn('taxPayments', annual[0])
        self.assertNotIn('taxReceivable', annual[0])
        partial = [dict(row, taxReceivable=0) for row in old]
        with self.assertRaisesRegex(ValueError, 'Incomplete tax'):
            dynamics.annual_rows(partial, 8)

    def test_construction_delay_and_book_value_match_analytic_solution(self):
        for year in range(1, 9):
            row = dynamics.at_year(self.rows, year)
            expected_wip = 40 * (1 - math.exp(-year / 2))
            expected_asset = (1000 * math.exp(-year / 10) + 200 * (1 - math.exp(-year / 10))
                              - 20 * (math.exp(-year / 2) - math.exp(-year / 10)) / (0.1 - 0.5))
            self.assertAlmostEqual(row['pipeline.constructionMoney[1]'], expected_wip, places=4)
            self.assertAlmostEqual(row['pipeline.constructionUnits[1]'], expected_wip / 10, places=5)
            self.assertAlmostEqual(row['pipeline.assets[1]'], expected_asset, places=3)
            self.assertAlmostEqual(row['pipeline.depreciation[1]'], expected_asset / 10, places=4)

    def test_slower_reduction_preserves_payroll_after_demand_decline(self):
        slow, fast = self.plant('slow'), self.plant('fast')
        self.assertAlmostEqual(dynamics.at_year(slow, 1)['services.staff[1]'], slow[0]['services.staff[1]'], places=5)
        for year in (2, 4, 8):
            a, b = dynamics.at_year(slow, year), dynamics.at_year(fast, year)
            self.assertGreater(a['services.staff[1]'], b['services.staff[1]'])
            self.assertGreater(a['cumulativePayroll'], b['cumulativePayroll'])
            self.assertAlmostEqual(a['capital.capacity[1]'], b['capital.capacity[1]'], places=5)

    def test_staffing_cut_saves_payroll_and_exposes_service_shortfall(self):
        row = dynamics.at_year(self.plant('cut'), 4)
        self.assertLess(row['services.staff[1]'], self.plant('cut')[0]['services.staff[1]'])
        self.assertGreater(row['services.unmetService[1]'], 0)
        self.assertGreater(row['cumulativeUnmet[1]'], 0)
        self.assertEqual(row['services.purchasedService[1]'], 0)

    def test_accrued_pension_expense_changes_result_but_not_cash_or_debt(self):
        base, pension = self.plant('base'), self.plant('pension')
        for year in range(1, 9):
            a, b = dynamics.at_year(base, year), dynamics.at_year(pension, year)
            self.assertAlmostEqual(a['debt'], b['debt'], places=4)
            self.assertAlmostEqual(a['cash'], b['cash'], places=4)
            self.assertAlmostEqual(b['finance.pensionAccrualBalance'], 85 * (year - 1), places=4)
            self.assertAlmostEqual(a['finance.cumulativeResult'] - b['finance.cumulativeResult'], 85 * (year - 1), places=3)

    def test_extra_cost_payment_timing_and_no_repetition_after_path_ends(self):
        base = dynamics.annual_rows(self.plant('extraReference'), 8)
        for name, costs, payments, balances in (
                ('extraDeferred', [0,50,0], [0,0,50], [0,50,0]),
                ('extraPaid', [0,50,0], [0,50,0], [0,0,0]),
                ('extraPrepaid', [0,0,50], [0,50,0], [0,-50,0])):
            rows = dynamics.annual_rows(self.plant(name), 8)
            for i, row in enumerate(rows):
                expense = costs[i] if i < 3 else 0
                payment = payments[i] if i < 3 else 0
                self.assertAlmostEqual(row['extraExpense'], expense, delta=2e-4)
                self.assertAlmostEqual(row['extraPayments'], payment, delta=2e-4)
                self.assertAlmostEqual(base[i]['result']-row['result'], expense, delta=2e-3)
                self.assertAlmostEqual(base[i]['operatingCash']-row['operatingCash'], payment, delta=2e-3)
                self.assertAlmostEqual(row['extraAccrualBalance'], balances[i] if i < 3 else 0, delta=2e-4)
        # A recognised but unpaid cost cannot itself create cash financing.
        a = dynamics.at_year(self.plant('extraReference'), 2)
        b = dynamics.at_year(self.plant('extraDeferred'), 2)
        self.assertAlmostEqual(a['cash'], b['cash'], delta=2e-4)
        self.assertAlmostEqual(a['debt'], b['debt'], delta=2e-4)

    def test_interest_shock_reprices_gradually_and_increases_debt(self):
        shock = self.plant('rateShock')
        base = self.plant('base')
        self.assertAlmostEqual(dynamics.at_year(shock, 1)['finance.portfolioRate'], 21 / 1040, places=7)
        for year in (2, 4, 8):
            row = dynamics.at_year(shock, year)
            expected = 0.05 + (21 / 1040 - 0.05) * math.exp(-(year - 1) / 3)
            self.assertAlmostEqual(row['finance.portfolioRate'], expected, places=7)
            self.assertGreater(row['debt'], dynamics.at_year(base, year)['debt'])

    def test_tax_rate_increase_is_not_offset_by_equalisation(self):
        for year in range(9):
            base, higher = dynamics.at_year(self.plant('base'), year), dynamics.at_year(self.plant('higherTax'), year)
            self.assertAlmostEqual(higher['tax'] / base['tax'], 0.227 / 0.217, places=7)
            self.assertAlmostEqual(higher['grants'], base['grants'], places=6)

    def test_surplus_repayment_cannot_create_negative_debt(self):
        for year in (1, 2):
            row = dynamics.at_year(self.rows, year)
            expected_debt = math.exp(-4 * year)
            self.assertAlmostEqual(row['surplus.debt'], expected_debt, places=6)
            self.assertAlmostEqual(row['surplus.cash'], 81 + 100 * year - (1 - expected_debt), places=5)

    def test_annual_flows_are_integrals_and_reconcile_stock_changes(self):
        rows = self.plant('base')
        annual = dynamics.annual_rows(rows, 8)
        self.assertGreater(abs(annual[0]['result'] - dynamics.at_year(rows, 1)['resultRate']), 0.1)
        for year, record in enumerate(annual, 1):
            previous = dynamics.at_year(rows, year - 1)
            self.assertAlmostEqual(record['debt'] - previous['debt'], record['borrowing'] - record['repayment'], places=5)
            self.assertAlmostEqual(record['cash'] - previous['cash'], record['operatingCash'] - record['investment']
                                   + record['borrowing'] - record['repayment'], places=5)
            # Includes financial income, other finance expense and the -1 cost rounding.
            expected = (record['tax'] + record['grants'] + record['operatingRevenue'] - record['payroll']
                        - record['otherOperatingExpense'] - record['pensionExpense'] - record['depreciation']
                        - record['disposalLoss'] - record['interest'] + 15 - 4 + 1)
            self.assertAlmostEqual(record['result'], expected, places=5)
            self.assertAlmostEqual(record['payroll'], sum(record[f'payroll{i}'] for i in (1, 2, 3)), places=5)
            self.assertAlmostEqual(record['otherOperatingExpense'], sum(record[f'otherExpense{i}'] for i in (1, 2, 3)), places=5)
        for record in dynamics.annual_rows(self.plant('constrained'), 8):
            for i in (1, 2, 3):
                self.assertGreaterEqual(record[f'unmetShare{i}'], -1e-10)
                self.assertLessEqual(record[f'unmetShare{i}'], 1 + 1e-10)

    def test_invalid_adjustment_time_is_rejected(self):
        with self.assertRaises(RuntimeError):
            dynamics.simulate(dynamics.scenario_source(parameters={'reductionYears': [0, 3, 3]}),
                              1, self.directory / 'invalid-time')

    def test_export_includes_calculated_parameters_and_override_dependencies(self):
        target = self.directory / 'parameter-export'
        dynamics.simulate(dynamics.scenario_source(parameters={'payrollShares': [0.5, 0.3, 0.2]}), 1, target)
        resolved = json.loads((target / 'resolved-parameters.json').read_text())
        self.assertEqual(resolved['workInProgress0']['value'], 99)
        self.assertAlmostEqual(sum(resolved[f'constructionMoney0[{i}]']['value'] for i in (1, 2, 3)), 99)
        self.assertAlmostEqual(resolved['staff0[1]']['value'], 2288 * 0.5 / 0.65)
        self.assertEqual(resolved['limitStaffChanges']['value'], False)
        self.assertEqual(resolved['serviceWeights[1,1]']['value'], 1)

    def test_impossible_migration_is_rejected(self):
        with self.assertRaises(RuntimeError):
            dynamics.simulate(dynamics.scenario_source(parameters={'migration': [-1e7, 0, 0, 0, 0]}),
                              1, self.directory / 'invalid-migration')


if __name__ == '__main__':
    unittest.main()
