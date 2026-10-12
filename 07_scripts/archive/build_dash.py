import json, re
t=open('dash_template.html').read()
D=json.load(open('dash_data.json'))
keep={k:D[k] for k in ['monthly','pareto','pareto_detail','client','supplier','mft_summary','mft_weekly','mft_base','unlocked','unlocked_family','a330_workmanship_jan_jun','a350_final','old_buckets_noncable','pareto_aside']}
page=t.replace('/*__DATA__*/', json.dumps(keep,ensure_ascii=False))
open('fto2_nc_findings.html','w').write(page)
open('test_page.html','w').write('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><style>body{margin:0}</style></head><body>'+page.replace('https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js','chart.umd.js')+'</body></html>')
chartjs=open('chart.umd.js').read()
off=page.replace('<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>','<script>\n'+chartjs.replace('</script','<\\/script')+'\n</script>')
off=re.sub(r'<link rel="preconnect"[^>]*>\n','',off)
off=re.sub(r'<link rel="stylesheet" href="https://fonts.googleapis.com[^>]*>\n','',off)
off='<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n'+off.replace('<div class="wrap">','</head><body style="margin:0">\n<div class="wrap">',1)+'\n</body></html>'
open('FTO2_NC_Findings_offline.html','w').write(off)
print('built', len(page), len(off))
