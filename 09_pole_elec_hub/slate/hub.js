// =============================================================================
//  Pôle Élec Quality Hub: configuration
// =============================================================================
//  This block is the only part to edit. Save, then refresh the page.
//
//  For each tool:
//    name        text on the card
//    description small line under the name ("" shows nothing)
//    icon        one of: trend-up, trending-up, trend-down, table, ban, alert,
//                        bars, pen, folder, form, eye, doc, check, shield,
//                        link, people, gear
//    color       colour of the wire and of the icon, for example "#2e8b3a"
//    link        address the card opens (in a new tab). While it still says
//                "A_COMPLETER", the card shows "Lien à compléter" and cannot
//                be clicked.
//    links       instead of link, several addresses, shown as buttons on the
//                card: [ { name: "GDrive", url: "https://..." }, ... ]
//                (a button still set to "A_COMPLETER" is not shown)
//    guide       optional extra link, shown as "Guide utilisateur"
//    soon        true = shown as "Bientôt disponible" and not clickable;
//                delete the line when the tool goes live
//
//  For each group: name, code (the tag on the header and in the drawing),
//  color.
//
//  The page has eight cards per row on a wide screen (four below 1240 px),
//  all the same size. Groups follow in the order below and share a row while
//  they fit in it (here Production & suivi, Assurance qualité and
//  Non-conformités: 1 + 3 + 4 tools; then Surveillance & amélioration and
//  Correctif: 4 + 4); otherwise a group starts a new row.
// =============================================================================

const HUB_CONFIG = {
  title: "Pôle Élec",
  subtitle: "Quality Hub",
  // in Slate the first name comes from {{user.firstName}}
  welcome: "MOHAMMAD, bienvenue sur le dashboard de la qualité Pôle Élec",

  groups: [
    {
      name: "Production & suivi", code: "PROD", color: "#b5602b",
      tools: [
        { name: "Suivi de la production", description: "Série, REC, Hors série", icon: "table", color: "#7b3fa8",
          links: [
            { name: "SÉRIE", url: "https://docs.google.com/spreadsheets/d/1ZiR6qiyPivrTtRxDHg43n0SApw3LIw15SGXKZb51e4c/edit?gid=0#gid=0" },
            { name: "REC", url: "https://docs.google.com/spreadsheets/d/1bUtT0iVMSCTUDYNmFqPJDf3PRiowM0yhojg6MTv4HfY/edit?gid=0#gid=0" },
            { name: "HS", url: "https://docs.google.com/spreadsheets/d/1_yBq9OYhxNDydYhHy8PQtPVJEFncIMymBPIpRG2Qb1o/edit?gid=0#gid=0" }
          ]
        }
      ]
    },
    {
      name: "Assurance qualité", code: "QA", color: "#2c6ad3",
      tools: [
        { name: "MyQA", description: "Site / GDrive", icon: "shield", color: "#2c97a4",
          link: "https://sites.google.com/airbus.com/myqa-tool-fr/accueil" },
        { name: "Qualif Indus", description: "C-SAAM (Zeinab)", icon: "gear", color: "#e67e22",
          links: [
            { name: "C-SAAM", url: "https://pac.intra.corp/airbus/ac/internal/1W79/zcsaam_new/start.html?saml2idp=1s14:hub-p:saml2#/IQRegister" },
            { name: "GDrive", url: "https://drive.google.com/drive/folders/1UEeVKj2uC1cDQbI-vEmktx6b4oJOP3o_" }
          ]
        },
        { name: "Qualif Personal", description: "Suivi qualifications", icon: "people", color: "#3498db",
          link: "https://drive.google.com/drive/folders/11ZpFytNOF6aQMO8YE3hDUy7XNBkCofaE" }
      ]
    },
    {
      name: "Non-conformités", code: "NC", color: "#d23f3f",
      tools: [
        { name: "NC Writing", description: "Rédaction des NC", icon: "pen", color: "#2c97a4",
          link: "https://core.skywise.com/workspace/foundry-slate/app/test123213213/page-1" },
        { name: "NC Dashboard", description: "Tableau de bord des NC", icon: "bars", color: "#038a9d",
          link: "https://core.skywise.com/workspace/foundry-slate/app/test123213213/home" },
        { name: "MFT", description: "Suivi MFT", icon: "people", color: "#9b59b6",
          link: "https://drive.google.com/drive/folders/15XZVV3-SY8bz5w8RxNUJmE0EKUbhVf5l" },
        { name: "NC Eradication", description: "Éradication des NC", icon: "trend-down", color: "#1d1673",
          link: "https://core.skywise.com/workspace/module/view/latest/ri.workshop.main.module.fe9aa8c0-22d4-4533-a04e-527c485347d1/similarityexplorer",
          guide: "https://sites.google.com/airbus.com/faq-nc-eradication/accueil", soon: true }
      ]
    },
    {
      name: "Surveillance & amélioration", code: "SURV", color: "#1d8a6b",
      tools: [
        { name: "Operational Surveillance", description: "DEMAT & GDrive", icon: "eye", color: "#5b4fc4",
          links: [
            { name: "DEMAT", url: "https://demat.intra.corp/DEMAT/#/" },
            { name: "GDrive", url: "https://drive.google.com/drive/folders/0AHx9eVFJ4lTlUk9PVA" }
          ]
        },
        { name: "Projets & Amélioration", description: "Projets et amélioration continue", icon: "trending-up", color: "#00a396",
          link: "https://drive.google.com/drive/folders/1N-L9s0Y1SpDH0I0hNf145ZOVnRkdxNrd" },
        { name: "Alert Quality", description: "Alertes qualité", icon: "alert", color: "#c41e1e",
          link: "https://drive.google.com/drive/folders/1jhbOjOa39LHXJM7v8tTE-_2Mv_f4RSuG" },
        { name: "FOD", description: "Foreign Object Debris", icon: "ban", color: "#e8483f",
          link: "https://sites.google.com/airbus.com/gsite-fod-airbus-electric-cent/accueil" }
      ]
    },
    {
      name: "Correctif", code: "CORR", color: "#8c3a9e",
      tools: [
        { name: "PPS", description: "Dashboard & GDrive", icon: "trend-up", color: "#2e8b3a",
          links: [
            { name: "Skywise", url: "https://core.skywise.com/workspace/contour-app/ri.contour.main.analysis.4c1518a3-f4ae-4180-b891-3a15bb56bb8e/dashboard/tab/8d3c9a1f-1597-4861-a90a-5c2f465ecf9c/edit" },
            { name: "GDrive", url: "https://drive.google.com/drive/folders/1XOzZbgKoalRyJSpLXolOK-w0mou9FcQQ" }
          ]
        },
        { name: "SARI Events", description: "CAPRI & GDrive", icon: "alert", color: "#e74c3c",
          links: [
            { name: "CAPRI", url: "https://peaswde0.eu.airbus.corp/airbus/ea/internal/1z43/z_capri_srv/home/index.html" },
            { name: "GDrive", url: "https://drive.google.com/drive/folders/1m0bYZ-A_lOKRfbfXfjfLyXN5pwDhOKlr" }
          ]
        },
        { name: "CPB", description: "DataStudio & GDrive", icon: "folder", color: "#00208b",
          links: [
            { name: "Lien", url: "https://datastudio.google.com/u/0/reporting/09b0a3bd-a6da-4be0-92e3-3805e3df8344/page/p_p2eag9tand/edit" },
            { name: "GDrive", url: "https://drive.google.com/drive/folders/1L9W2W8j5fqVKlQuw7skTLHCQ2S9oHP0K" }
          ]
        },
        { name: "QSR", description: "eQSR & GDrive", icon: "check", color: "#c2306f",
          links: [
            { name: "eQSR", url: "https://pac.intra.corp/airbus/ac/internal/G010/home/index.html?sap-client=001" },
            { name: "GDrive", url: "https://drive.google.com/drive/folders/1h_j30m-bGdgTYn2g9UWQ8-cHDq2S-JAf" }
          ]
        }
      ]
    }
  ]
};

const ICONS={
  "trend-up":'<path d="M3.5 3.5v17h17"/><path d="M7 15l4-4.5 3 2.5 5.5-6"/>',
  "table":'<rect x="3.5" y="4.5" width="17" height="15" rx="1.5"/><path d="M3.5 9.5h17M3.5 14.5h17M9.5 9.5v10"/>',
  "ban":'<circle cx="12" cy="12" r="8.5"/><path d="M6 18L18 6"/>',
  "alert":'<path d="M10.3 4.2L2.6 17.6A2 2 0 0 0 4.3 20.6h15.4a2 2 0 0 0 1.7-3L13.7 4.2a2 2 0 0 0-3.4 0z"/><path d="M12 9.5v4.5"/><path d="M12 17.2v.3"/>',
  "bars":'<path d="M4 20.5h16"/><path d="M7.5 17v-6M12 17V6.5M16.5 17v-8.5"/>',
  "pen":'<path d="M4 20h4.2L19.4 8.8a2 2 0 0 0 0-2.8l-1.4-1.4a2 2 0 0 0-2.8 0L4 15.8z"/><path d="M13.6 6.2l4.2 4.2"/>',
  "trend-down":'<path d="M3 7l6 6 4-4 8 8"/><path d="M15 17h6v-6"/>',
  "doc":'<path d="M6 2.8h8l4.5 4.5v13.9H6z"/><path d="M14 2.8v4.5h4.5M9 12h6M9 15.5h6"/>',
  "check":'<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V2.8h6V4"/><path d="M8.8 12.6l2.2 2.2 4.4-4.6"/>',
  "shield":'<path d="M12 3l7 3v5.5c0 4.5-3 8-7 9.5-4-1.5-7-5-7-9.5V6z"/><path d="M9 12l2 2 4-4"/>',
  "folder":'<path d="M3.5 6.5a2 2 0 0 1 2-2h4l2 2.5h7a2 2 0 0 1 2 2v8.5a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2z"/>',
  "link":'<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1.2 1.2"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1.2-1.2"/>',
  "people":'<circle cx="9" cy="8.5" r="3.2"/><path d="M3.5 19c.6-3.2 2.8-5 5.5-5s4.9 1.8 5.5 5"/><circle cx="17" cy="9.5" r="2.5"/><path d="M15.5 14.2c2.4-.2 4.4 1.3 5 4.3"/>',
  "gear":'<circle cx="12" cy="12" r="3.2"/><path d="M12 2.8v2.6M12 18.6v2.6M2.8 12h2.6M18.6 12h2.6M5.5 5.5l1.8 1.8M16.7 16.7l1.8 1.8M5.5 18.5l1.8-1.8M16.7 7.3l1.8-1.8"/>',
  "trending-up":'<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
  "form":'<rect x="4.5" y="3" width="15" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h4.5"/>',
  "eye":'<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>',
  "arrow":'<path d="M5 12h13M13 6.5l5.5 5.5-5.5 5.5"/>'
};
const $=s=>document.querySelector(s);
const esc=s=>String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const svgI=k=>'<svg viewBox="0 0 24 24" aria-hidden="true">'+(ICONS[k]||ICONS.link)+'</svg>';
const todo=u=>!u||/^A_COMPLETER/i.test(String(u).trim());
const noName=v=>!v||/^À COMPLÉTER/i.test(String(v).trim());

const C=HUB_CONFIG;
if(!C||!Array.isArray(C.groups)){
  $("#groups").innerHTML='<div class="err" style="grid-column:1/-1">la configuration HUB_CONFIG en haut du script contient une erreur.</div>';
} else {
  document.title=(C.title||"")+" "+(C.subtitle||"");
  $("#title").innerHTML=esc(C.title)+'<span>'+esc(C.subtitle)+'</span>';
  $("#welcome").textContent=C.welcome||"";

  let n=0;
  const html=C.groups.map((g,gi)=>{
    return '<section class="grp" style="--c:'+esc(g.color||"var(--copper)")+'">'
      +'<header class="g-hd"><span class="code">'+esc(g.code||g.name)+'</span><h2>'+esc(g.name)+'</h2><span class="rule"></span></header>'
      +'<div class="cards">'+(g.tools||[]).map((t,i)=>{
        const id="t"+(n++), w=esc(t.color||g.color||"#8592a5");
        // several links: one button each (the filled ones); one link: the whole card opens it
        const multi=Array.isArray(t.links), list=multi?t.links.filter(l=>l&&!todo(l.url)):[];
        const state=t.soon?"soon":(multi?list.length:!todo(t.link))?"link":"nolink";
        const cls=" "+state+(noName(t.name)?" noname":"")+(multi?" multi":"");
        const a=(u,label,c)=>'<a class="'+c+'" href="'+esc(u)+'" target="_blank" rel="noopener">'+esc(label)+'</a>';
        const guide=t.guide&&!todo(t.guide)?a(t.guide,"Guide utilisateur","guide"):'';
        const name=state==="link"&&!multi?a(t.link,t.name,"stretch"):esc(t.name);
        const foot=state==="soon"?'<span class="open">Bientôt disponible</span>'
                  :state==="nolink"?'<span class="open">Lien à compléter</span>'
                  :multi?'<span class="links">'+list.map(l=>a(l.url,l.name,"guide")).join("")+guide+'</span>'
                  :'<span class="open">Ouvrir '+svgI("arrow")+'</span>'+guide;
        const inner='<span class="c-top"><i class="wire"></i><i class="collar"></i><i class="ferr"></i><span class="ib">'+svgI(t.icon)+'</span>'
          +(state==="soon"?'<span class="soon-b">Bientôt</span>':'')+'</span>'
          +'<h3>'+name+'</h3>'+(t.description?'<p>'+esc(t.description)+'</p>':'')+'<span class="foot">'+foot+'</span>';
        return '<div class="card'+cls+'" data-id="'+id+'" style="--w:'+w+'">'+inner+'</div>';
      }).join("")+'</div></section>';
  });
  $("#groups").innerHTML=html.join("");

  // places on the card grid: eight compact cards per line on a wide screen, four below 1240 px.
  // Groups follow each other on a line while they fit, otherwise a new line starts. Each line is
  // a header row then its card rows (all 1fr, so every card row has the height of the tallest);
  // a 0 px row between two lines adds space.
  function layout(){
    const el=$("#groups"), COLS=innerWidth>=1240?8:4, lines=[];
    const place=C.groups.map(g=>{
      const n=(g.tools||[]).length, w=Math.max(1,Math.min(n,COLS)), k=Math.max(1,Math.ceil(n/COLS));
      let L=lines[lines.length-1];
      if(!L||L.used+w>COLS){L={used:0,k:1}; lines.push(L);}
      const at={L, c0:L.used+1, w};
      L.used+=w; L.k=Math.max(L.k,k);
      return at;
    });
    // where every line has a split between two groups (here after the 4th card), a wider gap
    const cuts=lines.length>1?[...Array(COLS-1).keys()].map(c=>c+1).filter(c=>lines.every(L=>place.some(P=>P.L===L&&P.c0-1===c))):[];
    const col=c=>c+cuts.filter(x=>x<c).length;
    const cols=[];
    for(let c=1;c<=COLS;c++){cols.push("minmax(0,1fr)"); if(cuts.includes(c)) cols.push("8px");}
    const tracks=[];
    lines.forEach((L,i)=>{
      if(i) tracks.push("0px");
      L.hr=tracks.length+1;
      tracks.push("auto", ...Array(L.k).fill("1fr"));
    });
    el.classList.toggle("dense",COLS===8);
    el.style.gridTemplateColumns=cols.join(" ");
    el.style.gridTemplateRows=tracks.join(" ");
    el.querySelectorAll(".grp").forEach((sec,gi)=>{
      const P=place[gi];
      sec.style.setProperty("--hr",P.L.hr);
      sec.classList.toggle("one",P.w===1);
      sec.style.setProperty("--hc",col(P.c0)+" / "+(col(P.c0+P.w-1)+1));
      sec.querySelectorAll(".card").forEach((c,i)=>{
        c.style.setProperty("--r",P.L.hr+1+Math.floor(i/P.w));
        c.style.setProperty("--cc",col(P.c0+i%P.w));
      });
    });
  }
  layout();
  addEventListener("resize",layout);

  // hero harness: connector, sleeve and tie-wraps on the trunk, one branch per group, one wire per tool
  (function(){
    const groups=C.groups.filter(g=>(g.tools||[]).length), N=groups.reduce((a,g)=>a+g.tools.length,0);
    const G=Math.min(5.2,70/Math.max(N,1)), Y=115, X0=96, XB=392, XE=596, top0=28, top1=202;
    const lane=i=>Y+(i-(N-1)/2)*G;
    const by=groups.map((g,i)=>groups.length===1?Y:top0+i*(top1-top0)/(groups.length-1));
    let defs='<defs><pattern id="braid" width="7" height="7" patternUnits="userSpaceOnUse"><rect width="7" height="7" fill="var(--braid-bg)"/>'
      +'<path d="M-1,1 L1,-1 M0,7 L7,0 M6,8 L8,6" stroke="var(--braid-a)" stroke-width="2"/><path d="M0,0 L7,7 M-1,6 L1,8 M6,-1 L8,1" stroke="var(--braid-b)" stroke-width="2"/></pattern>'
      +'<linearGradient id="al" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e9eef2"/><stop offset=".45" stop-color="#a2adb8"/><stop offset="1" stop-color="#55606b"/></linearGradient>'
      +'<linearGradient id="nut" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b9c3cc"/><stop offset=".5" stop-color="#76828e"/><stop offset="1" stop-color="#3f4952"/></linearGradient>'
      +'<linearGradient id="boot" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#454c55"/><stop offset=".35" stop-color="#22272d"/><stop offset="1" stop-color="#101316"/></linearGradient></defs>';
    let i=0, k0=0, wires="", ends="";
    groups.forEach((g,gi)=>{
      const k=g.tools.length;
      g.tools.forEach((t,j)=>{
        const y0=lane(i), y1=by[gi]+(j-(k-1)/2)*G;
        const d="M"+X0+","+y0+" H"+XB+" C"+(XB+96)+","+y0+" "+(XE-104)+","+y1+" "+(XE-10)+","+y1+" H"+(XE+12);
        wires+='<g class="hw" id="hw-t'+i+'" style="--w:'+esc(t.color||g.color||"#8592a5")+';--d:'+(2.2+((i*7)%5)*.35).toFixed(2)+'s;--dl:-'+((i*0.37)%2).toFixed(2)+'s">'
          +'<path class="o" d="'+d+'"/><path class="b" d="'+d+'"/><path class="h" d="'+d+'" transform="translate(-.6 -.7)"/><path class="p" d="'+d+'"/></g>';
        i++;
      });
      const h=k*G+14, top=by[gi]-h/2, code=String(g.code||g.name);
      ends+='<rect x="'+(XE-6)+'" y="'+(top+3)+'" width="22" height="'+(h-6)+'" rx="5" fill="url(#boot)"/>'
        +'<rect x="'+(XE+14)+'" y="'+top+'" width="36" height="'+h+'" rx="4" fill="url(#al)" stroke="#4b5560" stroke-width=".8"/>'
        +'<rect x="'+(XE+50)+'" y="'+(top+4)+'" width="6" height="'+(h-8)+'" rx="1.5" fill="#3a434c"/>'
        +'<rect x="'+(XE+62)+'" y="'+(by[gi]-11)+'" width="'+(code.length*8.4+16)+'" height="22" rx="5" fill="'+esc(g.color||"#b5602b")+'"/>'
        +'<text class="tagt" x="'+(XE+70)+'" y="'+(by[gi]+4.5)+'">'+esc(code)+'</text>';
      k0+=k;
    });
    const t0=lane(0)-5, t1=lane(N-1)+5, yc=Y;
    const tie=x=>'<rect x="'+(x-3.5)+'" y="'+(t0-1)+'" width="7" height="'+(t1-t0+2)+'" rx="2" fill="#1d2228"/><rect x="'+(x-5.5)+'" y="'+(t0-9)+'" width="11" height="9" rx="2" fill="#2a3037"/>';
    const conn='<rect x="6" y="'+(yc-44)+'" width="32" height="88" rx="5" fill="url(#nut)" stroke="#3a434c"/>'
      +Array.from({length:9},(_,m)=>'<path d="M'+(10+m*3.2)+','+(yc-40)+' V'+(yc+40)+'" stroke="rgba(0,0,0,.22)"/>').join("")
      +'<rect x="38" y="'+(yc-36)+'" width="28" height="72" rx="3" fill="url(#al)" stroke="#4b5560"/>'
      +'<path d="M66,'+(yc-34)+' L90,'+(yc-31)+' V'+(yc+31)+' L66,'+(yc+34)+' Z" fill="url(#al)" stroke="#4b5560"/>'
      +'<rect x="84" y="'+(yc-33)+'" width="36" height="66" rx="9" fill="url(#boot)"/>';
    const sleeve='<rect x="150" y="'+t0+'" width="196" height="'+(t1-t0)+'" rx="6" fill="url(#braid)"/>'
      +'<rect x="145" y="'+(t0-2)+'" width="12" height="'+(t1-t0+4)+'" rx="3" fill="url(#boot)"/><rect x="340" y="'+(t0-2)+'" width="12" height="'+(t1-t0+4)+'" rx="3" fill="url(#boot)"/>';
    $("#harness").innerHTML=defs+wires+sleeve+tie(132)+tie(370)+conn+ends;
  })();

  // a card lights its own wire in the harness
  const hs=$("#harness"), groupsEl=$("#groups");
  const lit=(id,on)=>{const w=document.getElementById("hw-"+id); if(w){w.classList.toggle("on",on); hs.classList.toggle("live",on);}};
  groupsEl.addEventListener("pointerover",e=>{const c=e.target.closest(".card"); if(c) lit(c.dataset.id,true);});
  groupsEl.addEventListener("pointerout",e=>{const c=e.target.closest(".card"); if(c&&!c.contains(e.relatedTarget)) lit(c.dataset.id,false);});
  groupsEl.addEventListener("focusin",e=>{const c=e.target.closest(".card"); if(c) lit(c.dataset.id,true);});
  groupsEl.addEventListener("focusout",e=>{const c=e.target.closest(".card"); if(c) lit(c.dataset.id,false);});
}
