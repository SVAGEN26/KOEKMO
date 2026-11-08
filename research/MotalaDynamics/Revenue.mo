within MotalaDynamics;
model Revenue "Illustrative revenue response, or explicit external reference-rate totals"
  parameter Real population0, exposure0, tax0, grants0, taxRate0, lagYears, equalisationOffset;
  parameter Boolean useExternal=false;
  parameter Boolean useExternalTax=false;
  input Real population, exposure, taxRate, taxIndex, grantIndex, externalTax, externalGrants;
  input Real externalTaxSettlement=0 "Signed collective settlement, mnkr/year; independent of own tax rate";
  output Real lagPopulation(start=population0,fixed=true), lagExposure(start=exposure0,fixed=true);
  output Real tax, grants, taxSettlement;
  output Real referenceGrants "Original internal grant path, also available in external mode";
  Real referenceTax;
equation
  der(lagPopulation)=(population-lagPopulation)/lagYears/yearSeconds;
  der(lagExposure)=(exposure-lagExposure)/lagYears/yearSeconds;
  referenceTax=tax0*taxIndex*lagExposure/exposure0;
  taxSettlement=if useExternal or useExternalTax then externalTaxSettlement else 0;
  tax=(if useExternal or useExternalTax then externalTax else referenceTax)*taxRate/taxRate0+taxSettlement;
  referenceGrants=grants0*grantIndex*lagPopulation/population0
    -equalisationOffset*(referenceTax-tax0*taxIndex*lagPopulation/population0);
  grants=if useExternal then externalGrants else referenceGrants;
  assert(taxRate>=0 and externalTax>=0,"Tax rate/reference tax must be nonnegative");
  annotation(Icon(coordinateSystem(extent={{-100,-75},{100,75}}),graphics={
      Rectangle(extent={{-100,-75},{100,75}},lineColor={40,95,140},fillColor={235,245,252},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-95,30},{95,65}},textString="Revenue",fontSize=21,textColor={40,95,140}),
      Text(extent={{-95,-27},{95,25}},textString="Tax and grants",fontSize=16,textColor={35,50,65}),
      Text(extent={{-95,-68},{95,-35}},textString="%name",fontSize=14,textColor={40,95,140})}),
    Diagram(coordinateSystem(extent={{-240,-130},{240,130}}),graphics={
      Text(extent={{-235,85},{235,125}},textString="Revenue",fontSize=22,textColor={35,50,65}),
      Rectangle(extent={{-230,-55},{-100,65}},lineColor={90,110,130},fillColor={245,248,250},fillPattern=FillPattern.Solid,radius=8),
      Rectangle(extent={{-65,-55},{65,65}},lineColor={40,95,140},fillColor={235,245,252},fillPattern=FillPattern.Solid,radius=8),
      Rectangle(extent={{100,-55},{230,65}},lineColor={50,120,90},fillColor={236,248,240},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-225,35},{-105,60}},textString="Inputs / assumptions",fontSize=13,textColor={35,50,65}),
      Text(extent={{-60,35},{60,60}},textString="States / update",fontSize=13,textColor={35,50,65}),
      Text(extent={{105,35},{225,60}},textString="Outputs",fontSize=13,textColor={35,50,65}),
      Text(extent={{-225,-48},{-105,32}},textString="Population / income\nTax rate / indices\nExternal paths",fontSize=13,textColor={35,50,65}),
      Text(extent={{-60,-48},{60,32}},textString="lagPopulation\nlagExposure\nLagged response",fontSize=13,textColor={35,50,65}),
      Text(extent={{105,-48},{225,32}},textString="Tax\nGrants\nTax settlement",fontSize=13,textColor={35,50,65}),
      Line(points={{-100,5},{-65,5}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Line(points={{65,5},{100,5}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Text(extent={{-235,-125},{235,-75}},textString="Revenue rates are annualised mnkr/year; external paths are optional.",fontSize=12,textColor={35,50,65})}),
    Documentation(info="<html><p>Revenue rates are annualised mnkr/year; external paths are optional. Diagram arrows summarize the equations; inputs are bound by the enclosing scenario.</p></html>"));
end Revenue;
