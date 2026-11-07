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
end Demography;
