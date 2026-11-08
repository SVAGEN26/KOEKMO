within MotalaResearch;
package Types "Units and annual conventions"
  type Money = Real(quantity="NominalSEKMillion") "mnkr";
  type People = Real(quantity="Persons",min=0) "Expected count; may be fractional";
  type PerPerson = Real(quantity="NominalSEKMillionPerPerson") "mnkr per person";
end Types;
