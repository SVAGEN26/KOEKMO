# Projektinstruktioner

## Beständigt projektminne

Läs `docs/project-memory.md` innan fortsatt arbete med modellens data, SKR-jämförelse eller datainsamling. Uppdatera filen när underlag hämtas, granskas eller importeras. Följ användarens önskemål att själv hämta offentliga underlag när det går.

## Kontrollera alltid mot faktiska utfall

Påstå aldrig något om hur det faktiskt blev utan att ha kontrollerat det i källan. Det gäller både utfall som modellen jämförs med och förklaringar av varför modellen avviker.

- Slå upp utfallet i den officiella källan: Motala kommuns årsredovisningar (resultaträkning och noter, kommunen och inte koncernen), SCB:s statistikdatabas och Kolada. Ange sida eller tabell.
- Kontrollera mot mer än en källa när det går, till exempel samma år i två årsredovisningar (jämförelsekolumnen) eller årsredovisningen mot SCB. Redovisa skillnader i stället för att välja den som passar.
- Varje prognos eller test som går att jämföra bakåt ska jämföras med vad som faktiskt hände: kör från ett tidigare basår och visa modellen bredvid utfallet, och bredvid kommunens budget och SKR:s prognos när de finns.
- Använd i sådana test bara data som var kända vid basåret. Senare utfall är facit, inte indata.
- Bakåt finns i projektet bokslutsserien 1998–2025 (`research/`), Motalas befolkning per ettårsålder från 2015, rikets folkmängd och livslängdstabeller från 2010, och Koladas nyckeltal från 2010 eller senare. SCB och Kolada har ofta längre serier än så att hämta. Hur långt bakåt det går beror på serien; ange gränsen när den nås. Historiska prognoser och antaganden (SKR:s cirkulär, kommunens budgetar, regeringens uppräkningsfaktor) finns bara för vissa år och måste hämtas per tillfälle.
- När ett utfall inte går att kontrollera, säg det rakt ut.
