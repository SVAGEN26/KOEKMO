within MotalaResearch.Components;
model Capital "Explicit investment scenario and blended depreciation proxy"
  parameter Types.Money assets0=2997;
  parameter Types.Money depreciation0=180;
  final parameter Real life=assets0/depreciation0;
  input Boolean tick;
  input Types.Money investment;
  discrete output Types.Money assets(start=assets0,fixed=true);
  discrete output Types.Money depreciation(start=depreciation0,fixed=true);
  discrete output Types.Money assetBalance(start=0,fixed=true);
initial equation
  assert(assets0>0 and depreciation0>0 and depreciation0<=assets0,"Invalid blended asset life");
equation
  assert(assets>=0 and investment>=0,"Negative assets/investment not supported");
  assert(abs(assetBalance)<1e-7,"Asset roll-forward failed");
algorithm
  when tick then
    depreciation := (pre(assets)+0.5*investment)/life;
    assets := pre(assets)+investment-depreciation;
    assetBalance := assets-pre(assets)-investment+depreciation;
  end when;
  annotation(Icon(coordinateSystem(extent={{-100,-75},{100,75}}),graphics={
      Rectangle(extent={{-100,-75},{100,75}},lineColor={155,95,35},fillColor={255,246,230},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-95,30},{95,65}},textString="Capital",fontSize=21,textColor={155,95,35}),
      Text(extent={{-95,-27},{95,25}},textString="Annual assets",fontSize=16,textColor={35,50,65}),
      Text(extent={{-95,-68},{95,-35}},textString="%name",fontSize=14,textColor={155,95,35})}),
    Diagram(coordinateSystem(extent={{-240,-130},{240,130}}),graphics={
      Text(extent={{-235,85},{235,125}},textString="Capital",fontSize=22,textColor={35,50,65}),
      Rectangle(extent={{-230,-55},{-100,65}},lineColor={90,110,130},fillColor={245,248,250},fillPattern=FillPattern.Solid,radius=8),
      Rectangle(extent={{-65,-55},{65,65}},lineColor={40,95,140},fillColor={235,245,252},fillPattern=FillPattern.Solid,radius=8),
      Rectangle(extent={{100,-55},{230,65}},lineColor={50,120,90},fillColor={236,248,240},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-225,35},{-105,60}},textString="Inputs / assumptions",fontSize=13,textColor={35,50,65}),
      Text(extent={{-60,35},{60,60}},textString="States / update",fontSize=13,textColor={35,50,65}),
      Text(extent={{105,35},{225,60}},textString="Outputs",fontSize=13,textColor={35,50,65}),
      Text(extent={{-225,-48},{-105,32}},textString="tick\nInvestment\nBlended asset life",fontSize=13,textColor={35,50,65}),
      Text(extent={{-60,-48},{60,32}},textString="assets\nAnnual roll-forward",fontSize=13,textColor={35,50,65}),
      Text(extent={{105,-48},{225,32}},textString="Depreciation\nAsset residual",fontSize=13,textColor={35,50,65}),
      Line(points={{-100,5},{-65,5}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Line(points={{65,5},{100,5}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Text(extent={{-235,-125},{235,-75}},textString="Investment execution and blended depreciation are scenario assumptions.",fontSize=12,textColor={35,50,65})}),
    Documentation(info="<html><p>Investment execution and blended depreciation are scenario assumptions.</p></html>"));
end Capital;
