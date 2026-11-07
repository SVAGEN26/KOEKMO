within ;
model MotalaBrowser "Browser wrapper: fixed array capacity, every scenario input a free parameter"
  extends Motala.Annual(
    final horizon=30,
    residualMigrationPath=zeros(30,5),
    wageGrowthPath=fill(0.03,30),
    priceGrowthPath=fill(0.02,30),
    pensionExpensePath=fill(190,30),
    pensionCashPaymentsPath=fill(190,30),
    referenceTax=fill(2330,30),
    referenceGrants=fill(987,30),
    referencePopulation=fill(43131,30),
    investmentPath=fill(413,30),
    interestRatePath=fill(21/1040,30),
    migrationDeltaPath=zeros(30),
    birthChangePath=zeros(30),
    serviceAdjustment=fill(0.5,3),
    serviceFixedShare=fill(0.25,3));
  annotation(Documentation(info="<html><p>This wrapper contains no model equations. OpenModelica compiles it once in the browser (wasm-jit); every scenario then re-runs the compiled model with -override. Independent literal bindings keep the annual arrays free parameters, so each element can be overridden. Thirty years is the compiled array capacity, not the forecast length: the host sets stopTime to the requested number of years.</p></html>"));
end MotalaBrowser;
