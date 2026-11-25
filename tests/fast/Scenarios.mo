within ;
package FastTests "Scenarier för snabbtesterna (tests/fast/test_model.py): Motala.Continuous med en ändring var"
  model Base "Standardantagandena"
    extends Motala.Continuous;
  end Base;

  model Shrinking "Färre invånare och inga investeringar"
    extends Motala.Continuous(migrationDelta = -300, investment = 0);
  end Shrinking;

  model WorkingCapital "Rörelsekapital och byggtid"
    extends Motala.Continuous(workingCapitalEnabled = true, constructionYears = 2);
  end WorkingCapital;

  model HigherTax "En krona högre skattesats och högre ränta"
    extends Motala.Continuous(taxRate = 22.7, interestRate = 0.05);
  end HigherTax;

  model TaxOnly "En krona högre skattesats"
    extends Motala.Continuous(taxRate = 22.7);
  end TaxOnly;

  model MoreArrivals "200 fler inflyttade per år"
    extends Motala.Continuous(migrationDelta = 200);
  end MoreArrivals;

  model NoReserve "Utan likviditetsreserv: kassan ligger kvar på bokslutets nivå"
    extends Motala.Continuous(liquidityPolicy = false);
  end NoReserve;

  model ReserveAtOnce "Likviditetsreserven gäller från första året"
    extends Motala.Continuous(reserveAdjustmentTime = 0);
  end ReserveAtOnce;
end FastTests;
