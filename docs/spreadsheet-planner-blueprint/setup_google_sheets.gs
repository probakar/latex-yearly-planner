/**
 * Run ONCE after importing Planner.xlsx into Google Sheets.
 *   Extensions > Apps Script > paste this file > Save > Run setupPlanner (authorise when asked).
 *
 * 1) turns the TRUE/FALSE cells into real checkboxes
 * 2) replaces the text bars (█░) with SPARKLINE bars that use the colours typed on Settings!C8 / C9
 *
 * NOTE: written from the blueprint; not executed in a live Google Sheet by the author - check the result.
 */
function setupPlanner() {
  var ss = SpreadsheetApp.getActive();
  var OPTS = '{"charttype","bar";"min",0;"max",1;"color1",Settings!$C$8;"color2",Settings!$C$9}';

  // ---- Month tab
  var month = ss.getSheetByName('Month');
  month.getRangeList(['B4:B8', 'B11:B25']).insertCheckboxes();

  for (var w = 1; w <= 6; w++) {
    var sh = ss.getSheetByName('W' + w);
    var boxes = ['B15:B19', 'B23:B27', 'BB6:BH26'];
    for (var d = 1; d <= 7; d++) {
      var c0 = 10 + 6 * (d - 1);                       // first column of day block
      boxes.push(a1_(47, c0) + ':' + a1_(56, c0));     // to-do checkboxes
    }
    sh.getRangeList(boxes).insertCheckboxes();

    // ---- bars
    for (d = 1; d <= 7; d++) {                         // daily to-do bar (pct sits in c0 of row 6)
      var col = 10 + 6 * (d - 1);
      sh.getRange(6, col + 1).setFormula('=SPARKLINE(' + a1_(6, col) + ',' + OPTS + ')');
    }
    for (var r = 6; r <= 27; r++) {                    // habit bars: % in BI (35+... col 61), bar in BJ (col 62)
      sh.getRange(r, 62).setFormula('=IF(' + a1_(r, 61) + '="","",SPARKLINE(' + a1_(r, 61) + ',' + OPTS + '))');
    }
    for (var t = 0; t < 5; t++) {                      // numeric trackers: hidden fractions in BM..BT
      var vr = 31 + 2 * t;
      for (d = 0; d < 8; d++) {                        // 7 days + average
        var frac = a1_(vr, 65 + d);                    // BM..BS days, BT average
        sh.getRange(vr + 1, 54 + d).setFormula('=IF(' + frac + '="","",SPARKLINE(' + frac + ',' + OPTS + '))');
      }
    }
  }
  SpreadsheetApp.getUi().alert('Planner ready: checkboxes and coloured bars applied.');
}

function a1_(row, col) {                               // 1-based row/col -> "BB6"
  var s = '';
  while (col > 0) { var m = (col - 1) % 26; s = String.fromCharCode(65 + m) + s; col = Math.floor((col - 1) / 26); }
  return s + row;
}
