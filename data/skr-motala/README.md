# Kommunvald och omräknad SKR-arbetsbok

Arbetsböckerna är SKR:s material och ingår inte i repot eller på sajten. Hämta
originalet, Prognosunderlag K 2026–2033 (cirkulär 26:28), från SKR:
https://skr.se/download/18.22a5529f1a0fb7804e67d572/1791283712510/Prognosunderlag-K-2026-2033-26028.xlsm
(sidan: https://skr.se/ekonomiochbudgetplanering/skatteunderlagsprognoserochmodellverktyg.8271.html)
och spara den som `data/Prognosunderlag-K-2026-2033-26028.xlsm`. Skripten
kontrollerar dess SHA-256 mot `selection-receipt.json`
(232479606a21b865e914bc91f9ddf7bee06b1e4abb8de16ba4b8e2ce30afb099). Repot innehåller
bara de belopp som lästs ut, med cellhänvisningar (`../skr-revenue-path.json`).

Original: ../Prognosunderlag-K-2026-2033-26028.xlsm, oförändrad. En arbetskopia
har kommunen 583 i Prognosunderlag!B1. Omräkning gjordes med LibreOffice 24.2.7.2.

- Prognosunderlag-Motala-0583-selected.xlsm: kommunvald kopia, ursprunglig VBA bevarad men aldrig körd.
- Prognosunderlag-Motala-0583.xlsx: mellanfil med VBA borttaget och formelcacher tömda.
- recalculated/Prognosunderlag-Motala-0583.xlsx: omräknade formler och användbara cachade värden.
- skr-map.json: explicit mappning av år, kommunval, skatter, bidrag och referensbefolkning.
- selection-receipt.json: original-/resultat-hash, beräkningsmotor och komponentavstämning.
- ../skr-revenue-path.json: importerad intäktsreferens, mnkr, 2026–2033.

Återskapa med `python3 scripts/recalculate_skr.py`, följt av
`python3 scripts/prepare_planning_inputs.py` och `npm run build`.
Omräknaren kräver den lokala runtime-kopian under .local/calc-runtime/root/.
Den hämtades med apt-get download för libreoffice-calc och dess saknade
beroenden (paketlista i .local/calc-runtime/packages.json), packades upp med
dpkg-deb -x och fick lokala sökvägar i fundamentalrc, sofficerc och unorc.
Registerfilerna från share/.registry kopierades till det lokala etc-registret.
Ingen systeminstallation gjordes. Makron är avstängda i en separat profil;
VBA tas dessutom bort ur den fil som skickas till LibreOffice.

Skatt hämtas från Blad 1 rad 38 (inklusive slutavräkningar). Bidrag hämtas från
rad 40 (inklusive utjämning, LSS och fastighetsavgift). Alla åtta år stäms av mot
rad 36. Befolkning är Blad 2 rad 29, 1 november året före intäktsåret.
Webbens scenariojusteringar är förenklade och kan avvika från dessa referensbelopp.
