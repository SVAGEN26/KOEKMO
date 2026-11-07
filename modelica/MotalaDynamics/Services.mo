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
  annotation(Icon(coordinateSystem(extent={{-100,-75},{100,75}}),graphics={
      Rectangle(extent={{-100,-75},{100,75}},lineColor={35,115,85},fillColor={234,248,240},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-95,30},{95,65}},textString="Services",fontSize=21,textColor={35,115,85}),
      Text(extent={{-95,-27},{95,25}},textString="Staff and delivery",fontSize=16,textColor={35,50,65}),
      Text(extent={{-95,-68},{95,-35}},textString="%name",fontSize=14,textColor={35,115,85})}),
    Diagram(coordinateSystem(extent={{-240,-130},{240,130}}),graphics={
      Text(extent={{-235,85},{235,125}},textString="Services",fontSize=22,textColor={35,50,65}),
      Rectangle(extent={{-230,-55},{-100,65}},lineColor={90,110,130},fillColor={245,248,250},fillPattern=FillPattern.Solid,radius=8),
      Rectangle(extent={{-65,-55},{65,65}},lineColor={40,95,140},fillColor={235,245,252},fillPattern=FillPattern.Solid,radius=8),
      Rectangle(extent={{100,-55},{230,65}},lineColor={50,120,90},fillColor={236,248,240},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-225,35},{-105,60}},textString="Inputs / assumptions",fontSize=13,textColor={35,50,65}),
      Text(extent={{-60,35},{60,60}},textString="States / update",fontSize=13,textColor={35,50,65}),
      Text(extent={{105,35},{225,60}},textString="Outputs",fontSize=13,textColor={35,50,65}),
      Text(extent={{-225,-48},{-105,32}},textString="Demand / capacity\nStaffing target\nSupplier limits",fontSize=13,textColor={35,50,65}),
      Text(extent={{-60,-48},{60,32}},textString="staff[1:n]\nHiring / reduction",fontSize=13,textColor={35,50,65}),
      Text(extent={{105,-48},{225,32}},textString="Own / purchased\nDelivered service\nUnmet demand",fontSize=13,textColor={35,50,65}),
      Line(points={{-100,5},{-65,5}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Line(points={{65,5},{100,5}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Text(extent={{-235,-125},{235,-75}},textString="Staff is in FTE; service volumes are demographic equivalents.",fontSize=12,textColor={35,50,65})}),
    Documentation(info="<html><p>Staff is in FTE; service volumes are demographic equivalents. Diagram arrows summarize the equations; inputs are bound by the enclosing scenario.</p></html>"));
end Services;
