within MotalaDynamics;
model Capital "Physical projects/capacity and financial WIP/book values remain separate"
  parameter Integer n=3;
  parameter Real capacity0[n], asset0[n], units0[n], money0[n];
  parameter Real physicalLife[n], accountingLife[n], constructionYears[n], closureYears[n], planningYears[n];
  parameter Boolean allowClosure=true, automaticInvestment=false;
  input Real desiredCapacity[n], unitCost[n], investmentBudget[n];
  output Real capacity[n](start=capacity0,each fixed=true);
  output Real constructionUnits[n](start=units0,each fixed=true);
  output Real constructionMoney[n](start=money0,each fixed=true);
  output Real assets[n](start=asset0,each fixed=true);
  output Real investment[n], requestedInvestment[n], commissionedUnits[n], commissionedMoney[n];
  output Real retirement[n], closure[n], depreciation[n], disposalLoss[n];
equation
  for i in 1:n loop
    retirement[i]=max(0,capacity[i])/physicalLife[i];
    closure[i]=if allowClosure then max(0,capacity[i]-desiredCapacity[i])/closureYears[i] else 0;
    requestedInvestment[i]=unitCost[i]*max(0,retirement[i]+(desiredCapacity[i]-capacity[i]-constructionUnits[i])/planningYears[i]);
    investment[i]=if automaticInvestment then min(investmentBudget[i],requestedInvestment[i]) else investmentBudget[i];
    commissionedUnits[i]=constructionUnits[i]/constructionYears[i];
    commissionedMoney[i]=constructionMoney[i]/constructionYears[i];
    der(constructionUnits[i])=(investment[i]/unitCost[i]-commissionedUnits[i])/yearSeconds;
    der(constructionMoney[i])=(investment[i]-commissionedMoney[i])/yearSeconds;
    der(capacity[i])=(commissionedUnits[i]-retirement[i]-closure[i])/yearSeconds;
    depreciation[i]=assets[i]/accountingLife[i];
    disposalLoss[i]=if capacity[i]>1e-9 then assets[i]*closure[i]/capacity[i] else 0;
    der(assets[i])=(commissionedMoney[i]-depreciation[i]-disposalLoss[i])/yearSeconds;
  end for;
  assert(min(investmentBudget)>=0 and min(unitCost)>0 and min(desiredCapacity)>=0,"Invalid investment/capacity input");
  assert(min(capacity)>=-1e-5 and min(assets)>=-1e-5 and min(constructionMoney)>=-1e-5 and min(constructionUnits)>=-1e-5,"Negative capital stock");
  annotation(Icon(coordinateSystem(extent={{-100,-75},{100,75}}),graphics={
      Rectangle(extent={{-100,-75},{100,75}},lineColor={155,95,35},fillColor={255,246,230},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-95,30},{95,65}},textString="Capital",fontSize=21,textColor={155,95,35}),
      Text(extent={{-95,-27},{95,25}},textString="Capacity and assets",fontSize=16,textColor={35,50,65}),
      Text(extent={{-95,-68},{95,-35}},textString="%name",fontSize=14,textColor={155,95,35})}),
    Diagram(coordinateSystem(extent={{-240,-130},{240,130}}),graphics={
      Text(extent={{-235,85},{235,125}},textString="Capital",fontSize=22,textColor={35,50,65}),
      Rectangle(extent={{-230,-55},{-100,65}},lineColor={90,110,130},fillColor={245,248,250},fillPattern=FillPattern.Solid,radius=8),
      Rectangle(extent={{-65,-55},{65,65}},lineColor={40,95,140},fillColor={235,245,252},fillPattern=FillPattern.Solid,radius=8),
      Rectangle(extent={{100,-55},{230,65}},lineColor={50,120,90},fillColor={236,248,240},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-225,35},{-105,60}},textString="Inputs / assumptions",fontSize=13,textColor={35,50,65}),
      Text(extent={{-60,35},{60,60}},textString="States / update",fontSize=13,textColor={35,50,65}),
      Text(extent={{105,35},{225,60}},textString="Outputs",fontSize=13,textColor={35,50,65}),
      Text(extent={{-225,-48},{-105,32}},textString="Capacity target\nInvestment budget\nUnit costs / lives",fontSize=13,textColor={35,50,65}),
      Text(extent={{-60,-48},{60,32}},textString="Capacity / WIP\nAssets\nConstruction",fontSize=13,textColor={35,50,65}),
      Text(extent={{105,-48},{225,32}},textString="Investment\nDepreciation\nDisposal losses",fontSize=13,textColor={35,50,65}),
      Line(points={{-100,5},{-65,5}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Line(points={{65,5},{100,5}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Text(extent={{-235,-125},{235,-75}},textString="Physical capacity and financial book values have separate balances.",fontSize=12,textColor={35,50,65})}),
    Documentation(info="<html><p>Physical capacity and financial book values have separate balances. Diagram arrows summarize the equations; inputs are bound by the enclosing scenario.</p></html>"));
end Capital;
