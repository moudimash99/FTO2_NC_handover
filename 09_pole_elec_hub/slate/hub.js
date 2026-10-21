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
//    guide       optional second link, shown as "Guide utilisateur"
//    soon        true = shown as "Bientôt disponible" and not clickable;
//                delete the line when the tool goes live
//
//  The first group is the main block (three cards per row, four from 10 tools
//  on). The other groups sit on the right, one under the other. Cards appear in
//  the order below.
//  Links taken from the current Slate app (A30 Quality Hub), 20 Oct 2026.
// =============================================================================

const HUB_CONFIG = {
  title: "Pôle Élec",
  subtitle: "Quality Hub",
  // in Slate the first name comes from {{user.firstName}}
  welcome: "MOHAMMAD, bienvenue sur le dashboard de la qualité Pôle Élec",

  groups: [
    {
      name: "Outils qualité", code: "OUTILS", color: "#b5602b",
      tools: [
        { name: "PPS", description: "Practical Problem Solving", icon: "trend-up", color: "#2e8b3a",
          link: "https://drive.google.com/drive/folders/1XOzZbgKoalRyJSpLXolOK-w0mou9FcQQ" },
        { name: "Serie Follow Up", description: "Suivi de la série", icon: "table", color: "#7b3fa8",
          link: "https://docs.google.com/spreadsheets/d/1ZiR6qiyPivrTtRxDHg43n0SApw3LIw15SGXKZb51e4c/edit?gid=0#gid=0" },
        { name: "FOD", description: "Foreign Object Debris", icon: "ban", color: "#e8483f",
          link: "https://drive.google.com/drive/folders/1Pc0LTYiEtla2-yroxx3rk49TaeUyyb8j" },
        { name: "Alert Quality", description: "Alertes qualité", icon: "alert", color: "#c41e1e",
          link: "https://drive.google.com/drive/folders/1jhbOjOa39LHXJM7v8tTE-_2Mv_f4RSuG" },
        { name: "NC Dashboard", description: "Tableau de bord des NC", icon: "bars", color: "#038a9d",
          link: "https://core.skywise.com/workspace/foundry-slate/app/ttttteqwffadsdasadsad/home" },
        { name: "NC Writing", description: "Rédaction des NC", icon: "pen", color: "#2c97a4",
          link: "https://core.skywise.com/workspace/code-workspaces/ri.foundry-container-service.main.container.fbafad4a-153e-476b-a137-69793a2112e3" },
        { name: "CPB", description: "", icon: "folder", color: "#00208b",
          link: "https://drive.google.com/drive/folders/1L9W2W8j5fqVKlQuw7skTLHCQ2S9oHP0K" },
        { name: "Projets & Amélioration", description: "Projets et amélioration continue", icon: "trending-up", color: "#00a396",
          link: "https://drive.google.com/drive/folders/1N-L9s0Y1SpDH0I0hNf145ZOVnRkdxNrd" },
        // new: link to fill in
        { name: "QSR", description: "", icon: "check", color: "#c2306f",
          link: "A_COMPLETER" },
        // new: link to fill in
        { name: "Operational Surveillance", description: "Surveillance opérationnelle", icon: "eye", color: "#5b4fc4",
          link: "A_COMPLETER" }
      ]
    },
    {
      name: "QCM", code: "QCM", color: "#1d1673",
      tools: [
        { name: "NC Eradication", description: "Éradication des NC", icon: "trend-down", color: "#1d1673",
          link: "https://core.skywise.com/workspace/module/view/latest/ri.workshop.main.module.fe9aa8c0-22d4-4533-a04e-527c485347d1/similarityexplorer",
          guide: "https://sites.google.com/airbus.com/faq-nc-eradication/accueil",
          soon: true }
      ]
    },
    {
      name: "QA Management", code: "QA", color: "#2c6ad3",
      tools: [
        // Form (DEMAT) removed on 21 Oct ("capri"). To bring it back, put this line above MyQA:
        // { name: "Form", description: "DEMAT", icon: "form", color: "#3a9a4a", link: "https://demat.intra.corp/DEMAT/#/" },
        { name: "MyQA", description: "MyQA tool", icon: "shield", color: "#2c97a4",
          link: "https://sites.google.com/airbus.com/myqa-tool-fr/accueil" }
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
    const main=gi===0, cols=main?((g.tools||[]).length>9?4:3):1;
    return '<section class="grp'+(main?' main':'')+'" style="--c:'+esc(g.color||"var(--copper)")+'">'
      +'<header class="g-hd"><span class="code">'+esc(g.code||g.name)+'</span><h2>'+esc(g.name)+'</h2><span class="rule"></span></header>'
      +'<div class="cards" style="--cols:'+cols+'">'+(g.tools||[]).map(t=>{
        const id="t"+(n++), w=esc(t.color||g.color||"#8592a5"), state=t.soon?"soon":todo(t.link)?"nolink":"link";
        const cls=" "+state+(noName(t.name)?" noname":"");
        const name=state==="link"?'<a class="stretch" href="'+esc(t.link)+'" target="_blank" rel="noopener">'+esc(t.name)+'</a>':esc(t.name);
        const foot=state==="link"?'<span class="open">Ouvrir '+svgI("arrow")+'</span>'+(t.guide&&!todo(t.guide)?'<a class="guide" href="'+esc(t.guide)+'" target="_blank" rel="noopener">Guide utilisateur</a>':'')
                  :state==="soon"?'<span class="open">Bientôt disponible</span>':'<span class="open">Lien à compléter</span>';
        const inner='<span class="c-top"><i class="wire"></i><i class="collar"></i><i class="ferr"></i><span class="ib">'+svgI(t.icon)+'</span>'
          +(state==="soon"?'<span class="soon-b">Bientôt</span>':'')+'</span>'
          +'<h3>'+name+'</h3>'+(t.description?'<p>'+esc(t.description)+'</p>':'')+'<span class="foot">'+foot+'</span>';
        return '<div class="card'+cls+'" data-id="'+id+'" style="--w:'+w+'">'+inner+'</div>';
      }).join("")+'</div></section>';
  });
  $("#groups").innerHTML=html[0]+'<div class="side">'+html.slice(1).join("")+'</div>';

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
