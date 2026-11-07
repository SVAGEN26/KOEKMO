within MotalaDynamics;
function annualOpeningFactor "Opening rate / previous annual total for exponential annual growth"
  input Real growth "Annual total growth fraction, greater than -1";
  output Real factor;
algorithm
  assert(growth > -1, "Annual growth must exceed -1");
  // If F(t)=F(0)*exp(log(1+g)*t), integral[-1,0] F(t)dt=previous total.
  // Taylor expansion avoids cancellation near zero (including exactly zero).
  factor := if abs(growth) < 1e-5 then 1 + growth/2 - growth^2/6 + growth^3/12
    else (1+growth)*log(1+growth)/growth;
end annualOpeningFactor;
