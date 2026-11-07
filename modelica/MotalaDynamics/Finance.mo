within MotalaDynamics;
model Finance "Cash-buffer policy, gradual debt repricing, and explicit expense/payment bridges"
  parameter Real debt0, cash0, rate0, rateYears, cashTarget, liquidityYears, repaymentYears;
  parameter Real taxReceivable0=0;
  input Real resultBeforeInterest, marketRate, depreciation, disposalLoss, pensionExpense, pensionPayments, investment;
  input Real extraExpense=0, extraPayments=0 "Additional expense is already deducted in resultBeforeInterest";
  input Real taxRevenue=0, taxPayments=taxRevenue "Recognised revenue and signed net cash receipt, mnkr/year";
  output Real debt(start=debt0,fixed=true), cash(start=cash0,fixed=true);
  output Real portfolioRate(start=rate0,fixed=true);
  output Real pensionAccrualBalance(start=0,fixed=true) "Cumulative expense minus payments, NOT actuarial liability";
  output Real extraAccrualBalance(start=0,fixed=true)
    "Additional expense minus payments since simulation start; positive payable, negative prepayment, not total provisions";
  output Real taxReceivable(start=taxReceivable0,fixed=true)
    "Net tax receivable; positive asset, negative payable, mnkr";
  output Real taxAccrualRate=taxRevenue-taxPayments "Annualised change in tax receivable, mnkr/year";
  output Real result, interest, operatingCash, cashBeforeFinancing, borrowing, repayment;
  output Real cumulativeResult(start=0,fixed=true), cumulativeOperatingCash(start=0,fixed=true);
  output Real cumulativeInvestment(start=0,fixed=true), cumulativeBorrowing(start=0,fixed=true);
  output Real cumulativeRepayment(start=0,fixed=true);
  output Real cumulativeTaxPayments(start=0,fixed=true);
  output Real debtResidual, cashResidual;
  Real surplus;
equation
  der(portfolioRate)=(marketRate-portfolioRate)/rateYears/yearSeconds;
  interest=portfolioRate*debt;
  result=resultBeforeInterest-interest;
  operatingCash=result+depreciation+disposalLoss+pensionExpense-pensionPayments+extraExpense-extraPayments-taxAccrualRate;
  cashBeforeFinancing=operatingCash-investment;
  surplus=cashBeforeFinancing+(cash-cashTarget)/liquidityYears;
  borrowing=max(0,-surplus);
  repayment=min(max(0,debt)/repaymentYears,max(0,surplus));
  der(debt)=(borrowing-repayment)/yearSeconds;
  der(cash)=(cashBeforeFinancing+borrowing-repayment)/yearSeconds;
  der(pensionAccrualBalance)=(pensionExpense-pensionPayments)/yearSeconds;
  der(extraAccrualBalance)=(extraExpense-extraPayments)/yearSeconds;
  der(taxReceivable)=taxAccrualRate/yearSeconds;
  der(cumulativeTaxPayments)=taxPayments/yearSeconds;
  der(cumulativeResult)=result/yearSeconds;
  der(cumulativeOperatingCash)=operatingCash/yearSeconds;
  der(cumulativeInvestment)=investment/yearSeconds;
  der(cumulativeBorrowing)=borrowing/yearSeconds;
  der(cumulativeRepayment)=repayment/yearSeconds;
  debtResidual=debt-debt0-cumulativeBorrowing+cumulativeRepayment;
  cashResidual=cash-cash0-cumulativeOperatingCash+cumulativeInvestment-cumulativeBorrowing+cumulativeRepayment;
  assert(debt>=-1e-5 and cash>=-1e-5,"Financing policy produced a negative stock");
  assert(pensionExpense>=0 and pensionPayments>=0,"Negative pension input");
  assert(extraExpense>=0 and extraPayments>=0,"Negative additional cost or payment input");
  annotation(Icon(coordinateSystem(extent={{-100,-75},{100,75}}),graphics={
      Rectangle(extent={{-100,-75},{100,75}},lineColor={105,75,145},fillColor={245,238,252},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-95,30},{95,65}},textString="Finance",fontSize=21,textColor={105,75,145}),
      Text(extent={{-95,-27},{95,25}},textString="Cash and debt",fontSize=16,textColor={35,50,65}),
      Text(extent={{-95,-68},{95,-35}},textString="%name",fontSize=14,textColor={105,75,145})}),
    Diagram(coordinateSystem(extent={{-240,-130},{240,130}}),graphics={
      Text(extent={{-235,85},{235,125}},textString="Finance",fontSize=22,textColor={35,50,65}),
      Rectangle(extent={{-230,-55},{-100,65}},lineColor={90,110,130},fillColor={245,248,250},fillPattern=FillPattern.Solid,radius=8),
      Rectangle(extent={{-65,-55},{65,65}},lineColor={40,95,140},fillColor={235,245,252},fillPattern=FillPattern.Solid,radius=8),
      Rectangle(extent={{100,-55},{230,65}},lineColor={50,120,90},fillColor={236,248,240},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-225,35},{-105,60}},textString="Inputs / assumptions",fontSize=13,textColor={35,50,65}),
      Text(extent={{-60,35},{60,60}},textString="States / update",fontSize=13,textColor={35,50,65}),
      Text(extent={{105,35},{225,60}},textString="Outputs",fontSize=13,textColor={35,50,65}),
      Text(extent={{-225,-48},{-105,32}},textString="Operating result\nInvestment / rate\nExpense / payments",fontSize=13,textColor={35,50,65}),
      Text(extent={{-60,-48},{60,32}},textString="Debt / cash\nPortfolio rate\nAccrual balances",fontSize=13,textColor={35,50,65}),
      Text(extent={{105,-48},{225,32}},textString="Interest / result\nBorrowing / repay\nOperating cash",fontSize=13,textColor={35,50,65}),
      Line(points={{-100,5},{-65,5}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Line(points={{65,5},{100,5}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Text(extent={{-235,-125},{235,-75}},textString="Expense and cash payment paths are separate; amounts are in mnkr.",fontSize=12,textColor={35,50,65})}),
    Documentation(info="<html><p>Expense and cash payment paths are separate; amounts are in mnkr. Diagram arrows summarize the equations; inputs are bound by the enclosing scenario.</p></html>"));
end Finance;
