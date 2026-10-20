// =============================================================================
//  Pôle Élec Quality Hub: configuration
// =============================================================================
//  This is the only file to edit. Keep it in the same folder as
//  pole_elec_hub.html, save it, then refresh the page.
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
//  The first group is the main block (three cards per row). The other groups
//  sit on the right, one under the other. Cards appear in the order below.
//  Links taken from the current Slate app (A30 Quality Hub), 20 Oct 2026.
// =============================================================================

window.HUB_CONFIG = {
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
        { name: "Projets & Amélioration", description: "Projets et amélioration continue", icon: "trending-up", color: "#00a396",
          link: "https://drive.google.com/drive/folders/1N-L9s0Y1SpDH0I0hNf145ZOVnRkdxNrd" },
        // new: link to fill in
        { name: "QSR", description: "", icon: "check", color: "#c2306f",
          link: "A_COMPLETER" },
        // new: link to fill in
        { name: "Operational Surveillance", description: "Surveillance opérationnelle", icon: "eye", color: "#5b4fc4",
          link: "A_COMPLETER" }
        // removed on 20 Oct; remove the two slashes to bring it back (add a comma after the line above)
        // { name: "CPB", description: "", icon: "folder", color: "#00208b", link: "https://drive.google.com/drive/folders/1L9W2W8j5fqVKlQuw7skTLHCQ2S9oHP0K" }
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
        { name: "Form", description: "DEMAT", icon: "form", color: "#3a9a4a",
          link: "https://demat.intra.corp/DEMAT/#/" },
        { name: "MyQA", description: "MyQA tool", icon: "shield", color: "#2c97a4",
          link: "https://sites.google.com/airbus.com/myqa-tool-fr/accueil" }
      ]
    }
  ]
};
