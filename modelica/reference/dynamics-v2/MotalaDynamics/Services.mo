within MotalaDynamics;
model Services "Staffing adjusts gradually; capacity shortages remain visible"
  parameter Integer n=3;
  parameter Real staff0[n], staffPerUnit[n], minimumStaff[n], hiringYears[n], reductionYears[n];
  parameter Boolean limitStaffChanges=false, limitExternalService=false;
  parameter Real maxStaffIncrease[n]=staff0, maxStaffDecrease[n]=staff0;
  input Real demand[n], capacity[n], staffingTarget[n], purchaseCoverage[n], productivity;
  input Real externalCapacity[n]=zeros(n);
  output Real staff[n](start=staff0,each fixed=true) "FTE, illustrative initial counts";
  output Real desiredStaff[n], staffIncrease[n], staffDecrease[n], staffCapacity[n];
  output Real ownService[n], purchasedService[n], unmetService[n], delivered[n];
equation
  for i in 1:n loop
    desiredStaff[i]=max(minimumStaff[i],staffPerUnit[i]*staffingTarget[i]*demand[i]/productivity);
    staffIncrease[i]=if limitStaffChanges then min(maxStaffIncrease[i],max(0,desiredStaff[i]-staff[i])/hiringYears[i])
      else max(0,desiredStaff[i]-staff[i])/hiringYears[i];
    staffDecrease[i]=if limitStaffChanges then min(maxStaffDecrease[i],max(0,staff[i]-desiredStaff[i])/reductionYears[i])
      else max(0,staff[i]-desiredStaff[i])/reductionYears[i];
    der(staff[i])=(staffIncrease[i]-staffDecrease[i])/yearSeconds;
    staffCapacity[i]=max(0,staff[i])*productivity/staffPerUnit[i];
    ownService[i]=min(demand[i],min(staffCapacity[i],max(0,capacity[i])));
    purchasedService[i]=if limitExternalService then min(externalCapacity[i],purchaseCoverage[i]*(demand[i]-ownService[i]))
      else purchaseCoverage[i]*(demand[i]-ownService[i]);
    delivered[i]=ownService[i]+purchasedService[i];
    unmetService[i]=demand[i]-delivered[i];
  end for;
  assert(min(demand)>=0 and min(staffingTarget)>=0 and productivity>0,"Invalid service demand/target/productivity");
  assert(min(purchaseCoverage)>=0 and max(purchaseCoverage)<=1,"purchaseCoverage must be in [0,1]");
  assert(min(externalCapacity)>=0 and min(maxStaffIncrease)>=0 and min(maxStaffDecrease)>=0,"Negative staffing/supplier capacity limit");
  assert(min(staff)>=-1e-6,"Negative staffing stock");
end Services;
