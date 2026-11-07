within MotalaDynamics;
model Demography "Continuous cohort balance; no endogenous service-to-migration claim"
  parameter Real p0[5], births0, deathRates[5], ageRates[5];
  parameter Boolean enabled=true;
  input Real migration[5] "Persons/year";
  input Real fertilityMultiplier;
  output Real p[5](start=p0,each fixed=true) "Persons";
  output Real population, births, deaths, netMigration, populationResidual;
  Real cumulativeChange(start=0,fixed=true) "Independent integral of external population flows";
equation
  births=if enabled then births0*p[4]/p0[4]*fertilityMultiplier else 0;
  deaths=if enabled then sum(deathRates.*p) else 0;
  netMigration=if enabled then sum(migration) else 0;
  for a in 1:5 loop
    der(p[a])=if enabled then ((if a==1 then births else ageRates[a-1]*p[a-1])
       -(ageRates[a]+deathRates[a])*p[a]+migration[a])/yearSeconds else 0;
  end for;
  population=sum(p);
  der(cumulativeChange)=(births-deaths+netMigration)/yearSeconds;
  populationResidual=population-sum(p0)-cumulativeChange;
  assert(fertilityMultiplier>=0,"Negative fertility multiplier");
  assert(min(p)>=-1e-6 and population>0,"Scenario exhausts an age cohort");
  annotation(Icon(coordinateSystem(extent={{-100,-75},{100,75}}),graphics={
      Rectangle(extent={{-100,-75},{100,75}},lineColor={40,95,140},fillColor={235,245,252},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-95,30},{95,65}},textString="Demography",fontSize=21,textColor={40,95,140}),
      Text(extent={{-95,-27},{95,25}},textString="Five age cohorts",fontSize=16,textColor={35,50,65}),
      Text(extent={{-95,-68},{95,-35}},textString="%name",fontSize=14,textColor={40,95,140})}),
    Diagram(coordinateSystem(extent={{-240,-130},{240,130}}),graphics={
      Text(extent={{-235,85},{235,125}},textString="Demography",fontSize=22,textColor={35,50,65}),
      Rectangle(extent={{-230,-55},{-100,65}},lineColor={90,110,130},fillColor={245,248,250},fillPattern=FillPattern.Solid,radius=8),
      Rectangle(extent={{-65,-55},{65,65}},lineColor={40,95,140},fillColor={235,245,252},fillPattern=FillPattern.Solid,radius=8),
      Rectangle(extent={{100,-55},{230,65}},lineColor={50,120,90},fillColor={236,248,240},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-225,35},{-105,60}},textString="Inputs / assumptions",fontSize=13,textColor={35,50,65}),
      Text(extent={{-60,35},{60,60}},textString="States / update",fontSize=13,textColor={35,50,65}),
      Text(extent={{105,35},{225,60}},textString="Outputs",fontSize=13,textColor={35,50,65}),
      Text(extent={{-225,-48},{-105,32}},textString="Migration\nFertility\nAge / death rates",fontSize=13,textColor={35,50,65}),
      Text(extent={{-60,-48},{60,32}},textString="p[1:5]\nCohort balances",fontSize=13,textColor={35,50,65}),
      Text(extent={{105,-48},{225,32}},textString="Population\nBirths / deaths\nNet migration",fontSize=13,textColor={35,50,65}),
      Line(points={{-100,5},{-65,5}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Line(points={{65,5},{100,5}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Text(extent={{-235,-125},{235,-75}},textString="Persons and persons/year; time is in seconds.",fontSize=12,textColor={35,50,65})}),
    Documentation(info="<html><p>Persons and persons/year; time is in seconds. Diagram arrows summarize the equations; inputs are bound by the enclosing scenario.</p></html>"));
end Demography;
