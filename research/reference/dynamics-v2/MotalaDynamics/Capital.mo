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
end Capital;
