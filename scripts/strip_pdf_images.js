// Replace every picture in a PDF with a blank image and mark visible ones "Bild borttagen".
//   mutool run scripts/strip_pdf_images.js in.pdf out.pdf
// Text, vector graphics and layout are kept. Prints the number of images replaced.
var args = scriptArgs;
if (args.length !== 2) throw new Error("usage: mutool run strip_pdf_images.js in.pdf out.pdf");
var doc = new PDFDocument(args[0]);

// One 1x1 white image shared by every replaced reference.
var white = new Pixmap(ColorSpace.DeviceRGB, [0, 0, 1, 1], false);
white.clear(255);
var blank = doc.addImage(new Image(white));
var font = doc.addSimpleFont(new Font("Helvetica"), "Latin");
var replaced = 0;
var seen = {};

// Some documents draw their text as tiny (e.g. 2x2) images shaped by a soft mask.
// Those are text, not pictures: keep every image of at most TINY pixels on both sides.
var TINY = 4;
function isPicture(width, height) { return width > TINY || height > TINY; }

// Swap image XObjects for the blank one, also inside forms and tiling patterns.
function scrub(resources) {
  if (!resources || !resources.isDictionary()) return;
  var xobjects = resources.get("XObject");
  if (xobjects && xobjects.isDictionary()) {
    xobjects.forEach(function (value, key) {
      var obj = value.resolve();
      var subtype = obj.get("Subtype");
      if (subtype && subtype.toString() === "/Image") {
        if (isPicture(obj.get("Width").valueOf(), obj.get("Height").valueOf())) {
          xobjects.put(key, blank);
          replaced++;
        }
      } else if (subtype && subtype.toString() === "/Form") {
        var id = value.isIndirect() ? value.asIndirect() : null;
        if (id === null || !seen[id]) { if (id !== null) seen[id] = true; scrub(obj.get("Resources")); }
      }
    });
  }
  var patterns = resources.get("Pattern");
  if (patterns && patterns.isDictionary()) {
    patterns.forEach(function (value) { scrub(value.resolve().get("Resources")); });
  }
  // Soft masks are forms too, and InDesign often draws a greyscale copy of a photo in them.
  var states = resources.get("ExtGState");
  if (states && states.isDictionary()) {
    states.forEach(function (value) {
      var mask = value.resolve().get("SMask");
      if (mask && mask.isDictionary()) {
        var group = mask.get("G");
        if (group) scrubForm(group);
      }
    });
  }
}

function scrubForm(ref) {
  var id = ref.isIndirect() ? ref.asIndirect() : null;
  if (id !== null && seen[id]) return;
  if (id !== null) seen[id] = true;
  scrub(ref.resolve().get("Resources"));
}

for (var i = 0; i < doc.countPages(); i++) {
  var page = doc.loadPage(i);
  // Where images are drawn, in page space (origin top left), before they disappear.
  var boxes = [];
  page.toStructuredText("preserve-images").walk({
    onImageBlock: function (bbox, transform, image) {
      if (isPicture(image.getWidth(), image.getHeight())) boxes.push(bbox);
    }
  });
  var pageObj = page.getObject();
  var resources = pageObj.get("Resources");
  scrub(resources);

  // Label images large enough to read; skip icons and pattern tiles.
  var label = "";
  var bounds = page.getBounds();
  var height = bounds[3] - bounds[1];
  boxes.forEach(function (box) {
    // Bleed images reach past the page edge; centre the label on the visible part.
    var b = [Math.max(box[0], bounds[0]), Math.max(box[1], bounds[1]), Math.min(box[2], bounds[2]), Math.min(box[3], bounds[3])];
    var w = b[2] - b[0], h = b[3] - b[1];
    if (w < 60 || h < 20) return;
    var size = Math.min(10, Math.max(6, h / 4));
    var x = b[0] + w / 2 - size * 3.6, y = height - (b[1] + h / 2) - size / 3;
    label += "q 0.4 g BT /FBildBorttagen " + size.toFixed(1) + " Tf " + x.toFixed(1) + " " + y.toFixed(1) +
      " Td (Bild borttagen) Tj ET Q\n";
  });
  if (label) {
    if (!resources || !resources.isDictionary()) { resources = doc.newDictionary(); pageObj.put("Resources", resources); }
    var fonts = resources.get("Font");
    if (!fonts || !fonts.isDictionary()) { fonts = doc.newDictionary(); resources.put("Font", fonts); }
    fonts.put("FBildBorttagen", font);
    // Wrap the original content in q/Q so its graphics state cannot leak into the label.
    var open = doc.addStream("q\n", {});
    var close = doc.addStream("Q\n" + label, {});
    var contents = pageObj.get("Contents");
    var array = doc.newArray();
    array.push(open);
    if (contents.isArray()) { for (var k = 0; k < contents.length; k++) array.push(contents.get(k)); }
    else array.push(contents);
    array.push(close);
    pageObj.put("Contents", array);
  }
}
doc.save(args[1], "garbage=compact,compress,compress-images");
print(replaced);
