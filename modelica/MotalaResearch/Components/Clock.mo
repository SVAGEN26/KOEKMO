within MotalaResearch.Components;
model Clock "Transition once at each whole model year; freeze after horizon"
  parameter Integer horizon(min=1)=3;
  output Boolean tick;
  discrete output Integer yearIndex(start=0,fixed=true);
initial equation
  assert(horizon>=1,"Positive forecast horizon required");
equation
  tick = sample(1,1) and time<=horizon;
  when tick then
    yearIndex = pre(yearIndex)+1;
  end when;
  annotation(Icon(coordinateSystem(extent={{-100,-75},{100,75}}),graphics={
      Rectangle(extent={{-100,-75},{100,75}},lineColor={40,95,140},fillColor={235,245,252},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-95,30},{95,65}},textString="Clock",fontSize=21,textColor={40,95,140}),
      Text(extent={{-95,-27},{95,25}},textString="Annual event",fontSize=16,textColor={35,50,65}),
      Text(extent={{-95,-68},{95,-35}},textString="%name",fontSize=14,textColor={40,95,140})}),
    Diagram(coordinateSystem(extent={{-240,-130},{240,130}}),graphics={
      Text(extent={{-235,85},{235,125}},textString="Clock",fontSize=22,textColor={35,50,65}),
      Rectangle(extent={{-230,-55},{-100,65}},lineColor={90,110,130},fillColor={245,248,250},fillPattern=FillPattern.Solid,radius=8),
      Rectangle(extent={{-65,-55},{65,65}},lineColor={40,95,140},fillColor={235,245,252},fillPattern=FillPattern.Solid,radius=8),
      Rectangle(extent={{100,-55},{230,65}},lineColor={50,120,90},fillColor={236,248,240},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-225,35},{-105,60}},textString="Inputs / assumptions",fontSize=13,textColor={35,50,65}),
      Text(extent={{-60,35},{60,60}},textString="States / update",fontSize=13,textColor={35,50,65}),
      Text(extent={{105,35},{225,60}},textString="Outputs",fontSize=13,textColor={35,50,65}),
      Text(extent={{-225,-48},{-105,32}},textString="Forecast horizon\nModel time",fontSize=13,textColor={35,50,65}),
      Text(extent={{-60,-48},{60,32}},textString="yearIndex\nOne event / year",fontSize=13,textColor={35,50,65}),
      Text(extent={{105,-48},{225,32}},textString="tick\nyearIndex",fontSize=13,textColor={35,50,65}),
      Line(points={{-100,5},{-65,5}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Line(points={{65,5},{100,5}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Text(extent={{-235,-125},{235,-75}},textString="Updates start at year 1 and freeze after the forecast horizon.",fontSize=12,textColor={35,50,65})}),
    Documentation(info="<html><p>Updates start at year 1 and freeze after the forecast horizon.</p></html>"));
end Clock;
