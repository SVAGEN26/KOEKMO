within MotalaDynamics;
package Examples "Controlled mechanisms; parameter values are scenarios, not forecasts"
  model Base
    Continuous plant;
    annotation(experiment(StartTime=0,StopTime=252460800,Interval=2629800,Tolerance=1e-8));
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
    extends Base(plant(pensionExpense=plant.pension0*exp(log(1+plant.pensionGrowth)*time/yearSeconds)
      +(if time>=yearSeconds then 85 else 0),
      pensionPayments=plant.pension0*exp(log(1+plant.pensionGrowth)*time/yearSeconds)));
  end PensionAccrual;
end Examples;
