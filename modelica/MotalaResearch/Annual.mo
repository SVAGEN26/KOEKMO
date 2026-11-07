within MotalaResearch;
model Annual "M1: inspect demography, ledger, capital and financing separately"
  parameter Integer horizon(min=1)=3;
  parameter Types.People p0[5];
  parameter Real deathRates[5];
  parameter Real residualMigration[5];
  parameter Real damping=1;
  parameter Types.People births0;
  parameter Types.Money revenue0, netCost0, financeNet0;
  parameter Types.PerPerson revenuePerPerson[horizon];
  parameter Types.PerPerson netCostPerPerson[horizon];
  parameter Types.PerPerson financeNetPerPerson[horizon];
  parameter Types.Money assets0=2997, depreciation0=180, debt0=1040, cash0=81;
  parameter Types.Money investmentPath[horizon]=fill(413,horizon);
  parameter Types.Money pensionAccrualMinusCashPath[horizon]=zeros(horizon);
  final parameter Boolean financingIsScenario=true
    "Financial forecasts do not identify pension cash payments or investment execution";
  Components.Clock clock(horizon=horizon)
    annotation(Placement(transformation(origin={-300,110},extent={{-75,-56},{75,56}})));
  Components.Demography demography(p0=p0,deathRates=deathRates,residualMigration=residualMigration,
    damping=damping,births0=births0,tick=clock.tick,yearIndex=clock.yearIndex)
    annotation(Placement(transformation(origin={-60,110},extent={{-75,-56},{75,56}})));
  Components.FiscalLedger ledger(revenue0=revenue0,netCost0=netCost0,financeNet0=financeNet0,
    tick=clock.tick,population=demography.population,revenuePerPerson=revenuePerPerson[pathIndex],
    netCostPerPerson=netCostPerPerson[pathIndex],financeNetPerPerson=financeNetPerPerson[pathIndex])
    annotation(Placement(transformation(origin={210,110},extent={{-75,-56},{75,56}})));
  Components.Capital capital(assets0=assets0,depreciation0=depreciation0,
    tick=clock.tick,investment=investmentPath[pathIndex])
    annotation(Placement(transformation(origin={-60,-110},extent={{-75,-56},{75,56}})));
  Components.Financing financing(debt0=debt0,cash0=cash0,tick=clock.tick,
    result=ledger.result,depreciation=capital.depreciation,investment=investmentPath[pathIndex],
    pensionAccrualMinusCash=pensionAccrualMinusCashPath[pathIndex])
    annotation(Placement(transformation(origin={210,-110},extent={{-75,-56},{75,56}})));
  output Integer yearIndex=clock.yearIndex;
  output Types.People population=demography.population;
  output Types.People p[5]=demography.p;
  output Types.Money taxAndGrants=ledger.taxAndGrants;
  output Types.Money netCost=ledger.netCost;
  output Types.Money financeNet=ledger.financeNet;
  output Types.Money result=ledger.result;
  output Types.Money debt=financing.debt, cash=financing.cash, assets=capital.assets;
protected
  Integer pathIndex;
equation
  pathIndex=max(1,clock.yearIndex);
  annotation(Icon(coordinateSystem(extent={{-100,-75},{100,75}}),graphics={
      Rectangle(extent={{-100,-75},{100,75}},lineColor={40,95,140},fillColor={235,245,252},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-95,30},{95,65}},textString="M1",fontSize=21,textColor={40,95,140}),
      Text(extent={{-95,-27},{95,25}},textString="Statistical paths\nAnnual accounting",fontSize=16,textColor={35,50,65}),
      Text(extent={{-95,-68},{95,-35}},textString="%name",fontSize=14,textColor={40,95,140})}),
    Diagram(coordinateSystem(extent={{-400,-230},{400,245}}),graphics={
      Text(extent={{-390,195},{390,235}},textString="M1: annual research candidate",fontSize=24,textColor={35,50,65}),
      Line(points={{-225,110},{-135,110}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Text(extent={{-225,120},{-135,155}},textString="tick / year",fontSize=13,textColor={35,50,65}),
      Line(points={{15,110},{135,110}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Text(extent={{20,120},{130,155}},textString="Population",fontSize=13,textColor={35,50,65}),
      Line(points={{210,54},{210,-54}},color={35,115,85},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Text(extent={{220,-25},{365,25}},textString="Annual result",fontSize=13,textColor={35,50,65}),
      Line(points={{15,-110},{135,-110}},color={155,95,35},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Text(extent={{15,-160},{135,-120}},textString="Depreciation",fontSize=13,textColor={35,50,65}),
      Text(extent={{-390,-225},{390,-175}},textString="Selected equation bindings. The common tick drives every component.\nPer-person fiscal paths and investment/pension paths are scenario inputs. Net cost includes depreciation.",fontSize=13,textColor={35,50,65})}),
    experiment(StartTime=0,StopTime=3,Interval=1),
    Documentation(info="<html><p>Run generated Scenario.mo for a fitted candidate. Time zero represents
closing base-year observations. Annual flows update at integer times and freeze after horizon.
Net cost includes depreciation: never subtract depreciation again from result.</p>
<p>Fiscal paths are independent statistical estimates in mnkr per person. Their source, fit and forecast
origin live in the run manifest. This model recomputes population and accounting from those inputs.
Financing remains a scenario: blended asset life, investment execution, pension cash payments and
working capital are not established by an aggregate accrual forecast.</p></html>"));
end Annual;
