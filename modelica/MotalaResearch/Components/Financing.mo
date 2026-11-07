within MotalaResearch.Components;
model Financing "Scenario cash bridge; excess cash repays debt before accumulating"
  parameter Types.Money debt0=1040;
  parameter Types.Money cash0=81;
  input Boolean tick;
  input Types.Money result;
  input Types.Money depreciation;
  input Types.Money investment;
  input Types.Money pensionAccrualMinusCash "Zero assumes pension expense equals cash payments";
  discrete output Types.Money operatingCash(start=0,fixed=true);
  discrete output Types.Money debt(start=debt0,fixed=true);
  discrete output Types.Money cash(start=cash0,fixed=true);
  discrete output Types.Money borrowing(start=0,fixed=true);
  discrete output Types.Money repayment(start=0,fixed=true);
  discrete output Types.Money debtBalance(start=0,fixed=true);
  discrete output Types.Money cashBalance(start=0,fixed=true);
protected
  discrete Real gap(start=0,fixed=true);
initial equation
  assert(debt0>=0 and cash0>=0,"Negative opening cash or debt");
equation
  assert(debt>=0,"Repayment exceeds debt");
  assert(abs(debtBalance)<1e-7 and abs(cashBalance)<1e-7,"Financing balance failed");
algorithm
  when tick then
    operatingCash := result+depreciation+pensionAccrualMinusCash;
    gap := investment-operatingCash;
    borrowing := max(0,gap);
    repayment := min(pre(debt),max(0,-gap));
    debt := pre(debt)+borrowing-repayment;
    cash := pre(cash)+operatingCash-investment+borrowing-repayment;
    debtBalance := debt-pre(debt)-borrowing+repayment;
    cashBalance := cash-pre(cash)-operatingCash+investment-borrowing+repayment;
  end when;
  annotation(Icon(coordinateSystem(extent={{-100,-75},{100,75}}),graphics={
      Rectangle(extent={{-100,-75},{100,75}},lineColor={105,75,145},fillColor={245,238,252},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-95,30},{95,65}},textString="Financing",fontSize=21,textColor={105,75,145}),
      Text(extent={{-95,-27},{95,25}},textString="Cash and debt",fontSize=16,textColor={35,50,65}),
      Text(extent={{-95,-68},{95,-35}},textString="%name",fontSize=14,textColor={105,75,145})}),
    Diagram(coordinateSystem(extent={{-240,-130},{240,130}}),graphics={
      Text(extent={{-235,85},{235,125}},textString="Financing",fontSize=22,textColor={35,50,65}),
      Rectangle(extent={{-230,-55},{-100,65}},lineColor={90,110,130},fillColor={245,248,250},fillPattern=FillPattern.Solid,radius=8),
      Rectangle(extent={{-65,-55},{65,65}},lineColor={40,95,140},fillColor={235,245,252},fillPattern=FillPattern.Solid,radius=8),
      Rectangle(extent={{100,-55},{230,65}},lineColor={50,120,90},fillColor={236,248,240},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-225,35},{-105,60}},textString="Inputs / assumptions",fontSize=13,textColor={35,50,65}),
      Text(extent={{-60,35},{60,60}},textString="States / update",fontSize=13,textColor={35,50,65}),
      Text(extent={{105,35},{225,60}},textString="Outputs",fontSize=13,textColor={35,50,65}),
      Text(extent={{-225,-48},{-105,32}},textString="tick / result\nDepreciation\nInvestment / pension",fontSize=13,textColor={35,50,65}),
      Text(extent={{-60,-48},{60,32}},textString="debt / cash\nCash bridge",fontSize=13,textColor={35,50,65}),
      Text(extent={{105,-48},{225,32}},textString="Operating cash\nBorrowing / repay\nBalance residuals",fontSize=13,textColor={35,50,65}),
      Line(points={{-100,5},{-65,5}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Line(points={{65,5},{100,5}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Text(extent={{-235,-125},{235,-75}},textString="The pension cash bridge is a scenario input, not an actuarial liability.",fontSize=12,textColor={35,50,65})}),
    Documentation(info="<html><p>The pension cash bridge is a scenario input, not an actuarial liability.</p></html>"));
end Financing;
