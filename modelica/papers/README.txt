PAPERS FOR THE MOTALA MODEL
==========================

The aim is an idealized, evidence-informed model that decision makers can inspect
and use to compare choices. Research informs candidate mechanisms; Motala data
must establish local parameter values and their uncertainty.

Local downloads and version control
----------------------------------
PDF originals and dated download receipts are local files excluded from Git.
The source catalogue and downloader remain versioned. Four existing originals
were moved here from scripts/ using their catalogued filenames during cleanup;
a fresh checkout must download its own copies. Consult download-receipts-*.json
for individual attempts; old failed receipts do not describe current availability.
No summary or HTML error page is stored as a paper.

You can download the following originals in your browser and place them here,
using the suggested filenames. Alternatively, in a network-enabled environment:

  python3 scripts/download_research.py

Run that command from the project root, or use the script's absolute path from
another working directory. The original
python3 papers/fetch.py command also works when run from modelica/.
Options:

  --list                      List the catalogue without accessing the network
  --only cellier-2008          Select a paper ID (repeat to select several)
  --output /path/to/papers     Choose where PDFs and receipts are saved
  --timeout 30 --retries 2     Network timeout and extra retry attempts (defaults)

The script preserves existing files, checks for PDF header/end markers and
records SHA256 hashes, source URLs and download errors. It retries transient
network failures and publishes each PDF only after the download is complete.
Inspect each PDF's title and contents after retrieval.
Its exit status is 1 if any paper remains unavailable. The Lund thesis needs
manual retrieval until its direct PDF link is known.

Reading order and original sources
----------------------------------
1. Konjunkturinstitutet (2024), Konjunkturläget mars 2024.
   Start with Demografisk framskrivning av kommunal konsumtion, printed page 44
   (also reproduced on page 78). Official methodology for demographic demand.
   Save as: ki-konjunkturlaget-mars-2024.pdf
   https://www.konj.se/media/3eojy3lo/konjunkturlaget-mars-2024.pdf

2. Kongnetiman, Fan, Walters and Osgood, Regional Economic Growth and Municipal
   Financial Planning: An Application of a System Dynamics Model to Calgary.
   Municipal model structure and feedbacks; Canadian institutions differ.
   Save as: calgary-municipal-financial-planning.pdf
   https://www.calgary.ca/content/dam/www/cfod/finance/documents/corporate-economics/other-reports/regional-economic-growth-and-municipal-financial-planning.pdf

3. Tim Starke (2021), Ausgabenseitige Effekte der demografischen Entwicklung
   auf die Kommunalfinanzen. Peer-reviewed German municipal evidence.
   Save as: starke-2021-demography-municipal-expenditure.pdf
   https://link.springer.com/content/pdf/10.1007/s41358-021-00269-0.pdf
   DOI: https://doi.org/10.1007/s41358-021-00269-0

4. François E. Cellier (2008), World3 in Modelica: Creating System Dynamics
   Models in the Modelica Framework. Implementation methodology.
   Save as: cellier-2008-world3-modelica.pdf
   https://people.inf.ethz.ch/cellier/Pubs/World/modelica_08_world3.pdf
   Library: https://github.com/modelica-3rdparty/SystemDynamics

5. Optional: Sofia Nilsson (2020), Att prognostisera det finansiella resultatet
   i svenska kommuner: en jämförelse mellan ett elastiskt nät och en baseline.
   Bachelor thesis; only the abstract has been reviewed so far.
   Open the repository record and follow its PDF link:
   https://lup.lub.lu.se/student-papers/record/9033365
   Save as: nilsson-2020-municipal-financial-forecasting.pdf

sources.json records source types, review scope and limits of applicability.
../data/model-research.json contains the earlier research notes.
../decision-support-design.txt connects these references to the proposed model
and decision-maker interface. That design is not an implemented replacement.
