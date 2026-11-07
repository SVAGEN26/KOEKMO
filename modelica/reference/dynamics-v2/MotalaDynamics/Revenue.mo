within MotalaDynamics;
model Revenue "Illustrative revenue response, or explicit external reference-rate totals"
  parameter Real population0, exposure0, tax0, grants0, taxRate0, lagYears, equalisationOffset;
  parameter Boolean useExternal=false;
  input Real population, exposure, taxRate, taxIndex, grantIndex, externalTax, externalGrants;
  output Real lagPopulation(start=population0,fixed=true), lagExposure(start=exposure0,fixed=true);
  output Real tax, grants;
  Real referenceTax;
equation
  der(lagPopulation)=(population-lagPopulation)/lagYears/yearSeconds;
  der(lagExposure)=(exposure-lagExposure)/lagYears/yearSeconds;
  referenceTax=tax0*taxIndex*lagExposure/exposure0;
  tax=(if useExternal then externalTax else referenceTax)*taxRate/taxRate0;
  grants=if useExternal then externalGrants else grants0*grantIndex*lagPopulation/population0
    -equalisationOffset*(referenceTax-tax0*taxIndex*lagPopulation/population0);
  assert(taxRate>=0 and externalTax>=0,"Tax rate/reference tax must be nonnegative");
end Revenue;
