within ;
package MotalaResearch "Independent Motala candidate: explicit annual population and fiscal flows"
  annotation(Icon(coordinateSystem(extent={{-100,-75},{100,75}}),graphics={
      Rectangle(extent={{-100,-75},{100,75}},lineColor={40,95,140},fillColor={235,245,252},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-95,30},{95,65}},textString="M1",fontSize=21,textColor={40,95,140}),
      Text(extent={{-95,-27},{95,25}},textString="Annual research model",fontSize=16,textColor={35,50,65}),
      Text(extent={{-95,-68},{95,-35}},textString="%name",fontSize=14,textColor={40,95,140})}),
    Documentation(info="<html><p>Research candidate beside the frozen Motala.Annual reference.
Money is nominal SEK million; time is counted in model years. Python estimates per-person fiscal paths
using only the declared observation vintage. This package executes cohort transitions, accrual accounting,
asset changes and a separately labelled financing scenario. No SKR forecast is a model input.</p>
<p>Inspect Annual, then its five components. Fiscal costs include depreciation. Pension expense already
belongs to these costs: only the difference between pension accrual and cash payment is added in the cash bridge.
The aggregate fiscal forecast does not infer a tax/grant split or sector budgets from missing data.</p></html>"));
end MotalaResearch;
