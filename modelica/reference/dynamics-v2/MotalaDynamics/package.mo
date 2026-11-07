within ;
package MotalaDynamics "Continuous municipal service and finance scenarios"
  constant Real yearSeconds=31557600 "Seconds per model year; all exposed flows are annual rates";
  annotation(Documentation(info="<html><p>Mechanism-based scenarios, not a fitted forecast.
Time is in seconds; divide by yearSeconds for years after 31 December 2025.
Simulate Examples.Base or another Examples model. Continuous is the component inside
these scenarios, not a standalone top-level input harness. All policy assumptions are parameters or public inputs.
See docs/dynamics-equations.md for derivation, research and parameter provenance.</p>
<p>Three service aggregates use demographic equivalents, not observed pupil/care volumes.
Initial staffing, capacities and their sector allocations are illustrative. Annual results
must be integrated; an end-of-year result rate is not an annual result.</p></html>"));
end MotalaDynamics;
