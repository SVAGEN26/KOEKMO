within MotalaResearch.Components;
model FiscalLedger "Per-person forecasts multiplied by population; reconcile annual result"
  parameter Types.Money revenue0;
  parameter Types.Money netCost0 "Includes depreciation";
  parameter Types.Money financeNet0;
  input Boolean tick;
  input Types.People population;
  input Types.PerPerson revenuePerPerson;
  input Types.PerPerson netCostPerPerson;
  input Types.PerPerson financeNetPerPerson;
  discrete output Types.Money taxAndGrants(start=revenue0,fixed=true);
  discrete output Types.Money netCost(start=netCost0,fixed=true);
  discrete output Types.Money financeNet(start=financeNet0,fixed=true);
  discrete output Types.Money result(start=revenue0-netCost0+financeNet0,fixed=true);
  output Types.Money ledgerResidual;
equation
  ledgerResidual = result-taxAndGrants+netCost-financeNet;
  assert(abs(ledgerResidual)<1e-7,"Fiscal ledger failed");
  assert(netCost>=0,"Net operating cost forecast must be nonnegative");
algorithm
  when tick then
    taxAndGrants := population*revenuePerPerson;
    netCost := population*netCostPerPerson;
    financeNet := population*financeNetPerPerson;
    result := taxAndGrants-netCost+financeNet;
  end when;
  annotation(Icon(coordinateSystem(extent={{-100,-75},{100,75}}),graphics={
      Rectangle(extent={{-100,-75},{100,75}},lineColor={35,115,85},fillColor={234,248,240},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-95,30},{95,65}},textString="Fiscal ledger",fontSize=21,textColor={35,115,85}),
      Text(extent={{-95,-27},{95,25}},textString="Annual accounts",fontSize=16,textColor={35,50,65}),
      Text(extent={{-95,-68},{95,-35}},textString="%name",fontSize=14,textColor={35,115,85})}),
    Diagram(coordinateSystem(extent={{-240,-130},{240,130}}),graphics={
      Text(extent={{-235,85},{235,125}},textString="Fiscal ledger",fontSize=22,textColor={35,50,65}),
      Rectangle(extent={{-230,-55},{-100,65}},lineColor={90,110,130},fillColor={245,248,250},fillPattern=FillPattern.Solid,radius=8),
      Rectangle(extent={{-65,-55},{65,65}},lineColor={40,95,140},fillColor={235,245,252},fillPattern=FillPattern.Solid,radius=8),
      Rectangle(extent={{100,-55},{230,65}},lineColor={50,120,90},fillColor={236,248,240},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-225,35},{-105,60}},textString="Inputs / assumptions",fontSize=13,textColor={35,50,65}),
      Text(extent={{-60,35},{60,60}},textString="States / update",fontSize=13,textColor={35,50,65}),
      Text(extent={{105,35},{225,60}},textString="Outputs",fontSize=13,textColor={35,50,65}),
      Text(extent={{-225,-48},{-105,32}},textString="tick / population\nRevenue per person\nCost / finance paths",fontSize=13,textColor={35,50,65}),
      Text(extent={{-60,-48},{60,32}},textString="Tax and grants\nNet cost\nFinance net",fontSize=13,textColor={35,50,65}),
      Text(extent={{105,-48},{225,32}},textString="Annual result\nLedger residual",fontSize=13,textColor={35,50,65}),
      Line(points={{-100,5},{-65,5}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Line(points={{65,5},{100,5}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Text(extent={{-235,-125},{235,-75}},textString="Amounts in mnkr; net cost already includes depreciation.",fontSize=12,textColor={35,50,65})}),
    Documentation(info="<html><p>Amounts in mnkr; net cost already includes depreciation.</p></html>"));
end FiscalLedger;
