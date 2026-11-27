within Kommunekonomi;
package Municipalities "Kommunerna: basår, befolkning och färdiga modeller för var och en"
  annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {40, 95, 140}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}, radius = 10), Text(textColor = {40, 95, 140}, extent = {{-90, -30}, {90, 30}}, textString = "13")}),
    Documentation(info = "<html><p>Ett paket per kommun i Östergötland. Varje paket har kommunens basår
(<code>Data</code>), modellen <code>Continuous</code>, som ärver
<a href=\"modelica://Kommunekonomi.Continuous.Economy\">Kommunekonomi.Continuous.Economy</a> med kommunens tal, och
exempel att simulera.</p>
<p>Motalas paket är skrivet för hand ur kommunens årsredovisningar. De tolv andra genereras av
<code>scripts/prepare_municipality.py</code> ur SCB:s räkenskapssammandrag och Kolada; redigera dem inte för hand.</p></html>"));
end Municipalities;
