# Test: getting an image or data out of a Slate Code Sandbox

Before a "download" or "copy" button is added to a page, this box finds which ways work in Slate.

1. On a test page of the Slate application, add a Code Sandbox (about 1,000 x 600 px).
2. Paste `download_test.html` into its HTML tab and `download_test.js` into its JavaScript tab. State: `{}`.
3. Press each button, one after the other. After each, look whether a file arrived in Downloads, or paste (Ctrl+V) into
   Excel or PowerPoint. The grey box says what each button tried.
4. Note the numbers that work. The pages will use the first one that works.

| Button | Way |
|---|---|
| 1, 2 | PNG image, downloaded through a link (data, blob) |
| 3, 4 | PNG image opened in a new tab, to save from there |
| 5 | PNG image copied to the clipboard |
| 6 | PNG image shown in the box, to right-click and save or copy |
| 7 | SVG image downloaded |
| 8, 9 | the data as a CSV file |
| 10, 11 | the data copied for Excel (two ways) |
| 12 | print, to save as PDF |
