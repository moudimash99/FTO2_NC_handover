FTO2 NC dashboard in a Slate code box
======================================

One file with everything: FTO2_NC_Dashboard_Slate.html. It opens as a normal page. It also holds the three
parts for a Slate code widget, each between START / END marker lines (CSS, HTML, JS).

The same three parts as separate files, one per box of the Slate code widget:

  fto2_slate.html  ->  HTML box
  fto2_slate.css   ->  CSS / style box
  fto2_slate.js    ->  JavaScript box

Paste each file whole (Ctrl+A, Ctrl+C in the file, Ctrl+V in the box). Do not paste the full
FTO2_NC_Dashboard.html into the HTML box: HTML boxes usually drop <script> tags, so the page stays empty.

The JavaScript file carries the data (NCs created 1 Jan - 28 Sep 2026), so nothing needs to be connected.
No outside resources are loaded (no fonts, no libraries). The styles only apply inside the dashboard.

If something goes wrong, a red box at the top of the dashboard says what failed.
If the box is empty and nothing shows, open the browser console (F12) and look for "[FTO2 dashboard]".

To refresh the data: run `python3 build/build_all.py`, then paste fto2_slate.js again.
