// @@STAMP@@
// Paste this whole file into a Slate function named f_fto2_views (Functions panel). It reads the two queries and the variable
// v_fto2_filters (the filters the page sends) and returns the views' model: every number, series and table the page shows.
var REF = @@REF@@;
@@MODEL@@
var nc = {{q_fto2_nc}}, def = {{q_fto2_def}}, filters = {{v_fto2_filters}};   // the views show no aléa: q_fto2_dis is not needed
if (!nc || !def) return null;   // a query still running
try {
  return FTO2Views.model({ nc: nc, def: def }, REF, filters || {});
} catch (e) {
  return { error: String((e && e.message) || e) };
}
