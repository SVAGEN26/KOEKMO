within ;
package FastTests "Scenarier för snabbtesterna (tests/fast/test_model.py): Kommunekonomi.Municipalities.Motala.Continuous med en ändring var"
  model Base "Standardantagandena"
    extends Kommunekonomi.Municipalities.Motala.Continuous;
  end Base;

  model Shrinking "Färre invånare och inga investeringar"
    extends Kommunekonomi.Municipalities.Motala.Continuous(migrationDelta = -300, investment = 0);
  end Shrinking;

  model WorkingCapital "Rörelsekapital och byggtid"
    extends Kommunekonomi.Municipalities.Motala.Continuous(workingCapitalEnabled = true, constructionYears = 2);
  end WorkingCapital;

  model HigherTax "En krona högre skattesats och högre ränta"
    extends Kommunekonomi.Municipalities.Motala.Continuous(taxRate = 22.7, interestRate = 0.05);
  end HigherTax;

  model TaxOnly "En krona högre skattesats"
    extends Kommunekonomi.Municipalities.Motala.Continuous(taxRate = 22.7);
  end TaxOnly;

  model MoreArrivals "200 fler inflyttade per år"
    extends Kommunekonomi.Municipalities.Motala.Continuous(migrationDelta = 200);
  end MoreArrivals;

  model NoReserve "Utan likviditetsreserv: kassan ligger kvar på bokslutets nivå"
    extends Kommunekonomi.Municipalities.Motala.Continuous(liquidityPolicy = false);
  end NoReserve;

  model ReserveAtOnce "Likviditetsreserven gäller från första året"
    extends Kommunekonomi.Municipalities.Motala.Continuous(reserveAdjustmentTime = 0);
  end ReserveAtOnce;

  model GivenPension "Pensionskostnaden given i mnkr i stället för att följa lönesumman"
    extends Kommunekonomi.Municipalities.Motala.Continuous(pensionFollowsPayroll = false, pensionExpensePath = fill(190, horizon));
  end GivenPension;

  model Prefinanced "Halva första årets investering betalas året efter och lånas i förväg"
    extends Kommunekonomi.Municipalities.Motala.Continuous(deferInvestmentShare = 0.5, prefinanceShare = 1);
  end Prefinanced;

  model InflationShock "Tre procentenheter extra inflation första året"
    extends Kommunekonomi.Municipalities.Motala.Continuous(inflationShock = 0.03);
  end InflationShock;

  model NoFeeIndexation "Samma chock, men taxor och avgifter följer inte med"
    extends Kommunekonomi.Municipalities.Motala.Continuous(inflationShock = 0.03, inflationRevenuePassThrough = 0);
  end NoFeeIndexation;

  model GrantParts "Bidragen per del; statens ram följer rikets skatteunderlag"
    extends Kommunekonomi.Municipalities.Motala.Continuous(grantsByComponent = true);
  end GrantParts;

  model GrantPartsHeld "Bidragen per del; regleringsbidraget per invånare ligger kvar i kronor"
    extends Kommunekonomi.Municipalities.Motala.Continuous(grantsByComponent = true, stateFrameFollowsTaxBase = false);
  end GrantPartsHeld;

  model Cloudburst "Ett skyfall i juli 2027: 56 mnkr i reparationer under ett halvår"
    extends Kommunekonomi.Municipalities.Motala.Continuous(oneOffCost = 56, oneOffCostTime = 2027.5);
  end Cloudburst;

  model OwnMigration "Flyttningen tas bara från kommunens egna två år"
    extends Kommunekonomi.Municipalities.Motala.Continuous(migrationGroupWeight = 0);
  end OwnMigration;

  model GroupMigration "Flyttningen tas från kommunens grupp enligt SKR i stället för kommunens egna två år"
    extends Kommunekonomi.Municipalities.Motala.Continuous(migrationGroupWeight = 1);
  end GroupMigration;

end FastTests;
