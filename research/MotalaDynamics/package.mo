within ;
package MotalaDynamics "Continuous municipal service and finance scenarios"
  constant Real yearSeconds=31557600 "Seconds per model year; all exposed flows are annual rates";
  annotation(Icon(coordinateSystem(extent={{-100,-75},{100,75}}),graphics={
      Rectangle(extent={{-100,-75},{100,75}},lineColor={40,95,140},fillColor={235,245,252},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-95,30},{95,65}},textString="M2",fontSize=21,textColor={40,95,140}),
      Text(extent={{-95,-27},{95,25}},textString="Continuous scenarios",fontSize=16,textColor={35,50,65}),
      Text(extent={{-95,-68},{95,-35}},textString="%name",fontSize=14,textColor={40,95,140})}),
    Documentation(info="<html><p>Mechanism-based scenarios, not a fitted forecast.
Time is in seconds; divide by yearSeconds for years after 31 December 2025.
Simulate Examples.Base or another Examples model. Continuous is the component inside
these scenarios, not a standalone top-level input harness. All policy assumptions are parameters or public inputs.
See research/dynamics-equations.md for derivation, research and parameter provenance.</p>
<p>Three service aggregates use demographic equivalents, not observed pupil/care volumes.
Initial staffing, capacities and their sector allocations are illustrative. Annual results
must be integrated; an end-of-year result rate is not an annual result.</p></html>"));
end MotalaDynamics;
