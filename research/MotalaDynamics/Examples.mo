within MotalaDynamics;
package Examples "Controlled mechanisms; parameter values are scenarios, not forecasts"
  model Base
    Continuous plant
      annotation(Placement(transformation(extent={{-100,-75},{100,75}})));
    annotation(Icon(coordinateSystem(extent={{-100,-75},{100,75}}),graphics={
        Rectangle(extent={{-100,-75},{100,75}},lineColor={40,95,140},fillColor={235,245,252},fillPattern=FillPattern.Solid,radius=8),
        Text(extent={{-95,30},{95,65}},textString="M2 scenario",fontSize=21,textColor={40,95,140}),
        Text(extent={{-95,-27},{95,25}},textString="Inspect plant\nfor model structure",fontSize=16,textColor={35,50,65}),
        Text(extent={{-95,-68},{95,-35}},textString="%name",fontSize=14,textColor={40,95,140})}),
      Diagram(coordinateSystem(extent={{-200,-160},{200,160}}),graphics={
        Text(extent={{-195,115},{195,155}},textString="Continuous municipal scenario",fontSize=22,textColor={35,50,65}),
        Text(extent={{-195,-150},{195,-95}},textString="Double-click plant to open its component diagram.\nSimulate for 8 years (252460800 seconds); plot plant.modelYear for years.\nParameters and input bindings define the chosen scenario.",fontSize=12,textColor={35,50,65})}),
      experiment(StartTime=0,StopTime=252460800,Interval=2629800,Tolerance=1e-8));
  end Base;

  model SchoolDecline "15 percent lower education demand from year 1"
    extends Base(plant(demographyEnabled=false,
      demandMultiplier={if time>=yearSeconds then 0.85 else 1,1,1}));
  end SchoolDecline;

  model FastAdjustment "Same demand change, faster education staffing reduction"
    extends SchoolDecline(plant(reductionYears={0.5,3,3}));
  end FastAdjustment;

  model StaffingCut "Lower staffing target with no purchased replacement: show service gap"
    extends Base(plant(demographyEnabled=false,purchaseCoverage=zeros(3),
      staffingTarget={if time>=yearSeconds then 0.8 else 1,1,1}));
  end StaffingCut;

  model InterestShock "Market rate rises to five percent after one year"
    extends Base(plant(marketRate=if time>=yearSeconds then 0.05 else plant.interestRate0));
  end InterestShock;

  model SupplyConstraint "20 percent higher care demand, capped staffing increases and bought service"
    extends Base(plant(demographyEnabled=false,limitStaffChanges=true,limitExternalService=true,
      demandMultiplier={1,if time>=yearSeconds then 1.2 else 1,1}));
  end SupplyConstraint;

  model PensionAccrual "Expense increases, payments remain on the same path"
    extends Base(plant(pensionExpense=plant.pension0*plant.pensionOpening*exp(log(1+plant.pensionGrowth)*time/yearSeconds)
      +(if time>=yearSeconds then 85 else 0),
      pensionPayments=plant.pension0*plant.pensionOpening*exp(log(1+plant.pensionGrowth)*time/yearSeconds)));
  end PensionAccrual;

  model ExtraCost "50 mnkr additional expense in year 2, paid 20 then 30 in year 3"
    extends Base(plant(extraCostPath={0,50,0},extraCostPaymentPath={0,20,30}));
  end ExtraCost;

  model TaxSettlement "50 mnkr settlement in year 2, received in year 3; reference tax and grants fixed"
    extends Base(plant(useExternalRevenue=true,
      externalTax=plant.tax0,externalGrants=plant.grants0,
      externalTaxSettlement=if time>=yearSeconds and time<2*yearSeconds then 50 else 0,
      taxPayments=plant.tax0*plant.taxRate/plant.taxRate0
        +(if time>=2*yearSeconds and time<3*yearSeconds then 50 else 0)));
  end TaxSettlement;
end Examples;
