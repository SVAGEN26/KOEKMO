within MotalaResearch.Components;
model Demography "Survival, ageing, births and damped cohort residual migration"
  parameter Types.People p0[5];
  parameter Real deathRates[5];
  parameter Real residualMigration[5];
  parameter Real damping(min=0,max=1)=1 "Retained fraction per forecast year";
  parameter Types.People births0;
  input Boolean tick;
  input Integer yearIndex;
  discrete output Types.People p[5](start=p0,each fixed=true);
  discrete output Types.People population(start=sum(p0),fixed=true);
  discrete output Real births(start=births0,fixed=true);
  discrete output Real deaths(start=0,fixed=true);
  discrete output Real migration(start=0,fixed=true);
  discrete output Real populationBalance(start=0,fixed=true);
protected
  discrete Real survivors[5](each start=0,each fixed=true);
  discrete Real ageOut[5](each start=0,each fixed=true);
initial equation
  assert(min(p0)>0,"All five initial cohorts must be positive");
  assert(min(deathRates)>=0 and max(deathRates)<=1,"Mortality must be in [0,1]");
  assert(damping>=0 and damping<=1 and births0>=0,"Invalid demographic assumptions");
equation
  assert(min(p)>=0 and population>0,"Scenario exhausts a population cohort");
  assert(abs(populationBalance)<1e-7,"Population conservation failed");
algorithm
  when tick then
    births := births0*pre(p[4])/p0[4];
    deaths := sum(pre(p).*deathRates);
    survivors := pre(p).*(ones(5)-deathRates);
    ageOut := {survivors[1]/7,survivors[2]/9,survivors[3]/3,survivors[4]/46,0};
    for i in 1:5 loop
      p[i] := survivors[i]-ageOut[i]+(if i==1 then births else ageOut[i-1])
        +residualMigration[i]*damping^yearIndex;
    end for;
    population := sum(p);
    migration := sum(residualMigration)*damping^yearIndex;
    populationBalance := population-sum(pre(p))-births+deaths-migration;
  end when;
  annotation(Icon(coordinateSystem(extent={{-100,-75},{100,75}}),graphics={
      Rectangle(extent={{-100,-75},{100,75}},lineColor={40,95,140},fillColor={235,245,252},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-95,30},{95,65}},textString="Demography",fontSize=21,textColor={40,95,140}),
      Text(extent={{-95,-27},{95,25}},textString="Annual cohorts",fontSize=16,textColor={35,50,65}),
      Text(extent={{-95,-68},{95,-35}},textString="%name",fontSize=14,textColor={40,95,140})}),
    Diagram(coordinateSystem(extent={{-240,-130},{240,130}}),graphics={
      Text(extent={{-235,85},{235,125}},textString="Demography",fontSize=22,textColor={35,50,65}),
      Rectangle(extent={{-230,-55},{-100,65}},lineColor={90,110,130},fillColor={245,248,250},fillPattern=FillPattern.Solid,radius=8),
      Rectangle(extent={{-65,-55},{65,65}},lineColor={40,95,140},fillColor={235,245,252},fillPattern=FillPattern.Solid,radius=8),
      Rectangle(extent={{100,-55},{230,65}},lineColor={50,120,90},fillColor={236,248,240},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-225,35},{-105,60}},textString="Inputs / assumptions",fontSize=13,textColor={35,50,65}),
      Text(extent={{-60,35},{60,60}},textString="States / update",fontSize=13,textColor={35,50,65}),
      Text(extent={{105,35},{225,60}},textString="Outputs",fontSize=13,textColor={35,50,65}),
      Text(extent={{-225,-48},{-105,32}},textString="tick / yearIndex\nBirths / mortality\nMigration residuals",fontSize=13,textColor={35,50,65}),
      Text(extent={{-60,-48},{60,32}},textString="p[1:5]\nAnnual cohort step",fontSize=13,textColor={35,50,65}),
      Text(extent={{105,-48},{225,32}},textString="Population\nBirths / deaths\nMigration",fontSize=13,textColor={35,50,65}),
      Line(points={{-100,5},{-65,5}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Line(points={{65,5},{100,5}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Text(extent={{-235,-125},{235,-75}},textString="Five age cohorts; annual flows in persons. Residuals include reconciliation.",fontSize=12,textColor={35,50,65})}),
    Documentation(info="<html><p>Cohorts are 0-6, 7-15, 16-18, 19-64, 65+.
Uniform within-cohort ageing is retained for compatibility with available data.
Residual migration includes statistical reconciliation and cohort approximation errors.
Damping is selected only using completed training years, never future observations.</p></html>"));
end Demography;
