// =============================================================================
//  Pôle Élec Quality Hub: configuration
// =============================================================================
//  This is the only file to edit. Keep it in the same folder as
//  pole_elec_hub.html, save it, then refresh the page.
//
//  For each tool:
//    name        text on the card
//    description small line under the name ("" shows nothing)
//    icon        one of: trend-up, table, ban, alert, bars, pen, trend-down,
//                        doc, check, shield, folder, link, people, gear
//    color       colour of the wire and of the icon, for example "#2e9e5b"
//    link        the Skywise address of the tool: paste it between the quotes.
//                While it still says "A_COMPLETER", the card shows
//                "Lien à compléter" and cannot be clicked.
//
//  The first group is the main block (three cards per row, as in the current
//  hub). The other groups sit on the right, one under the other.
//  The order of the cards on the page is the order below.
// =============================================================================

window.HUB_CONFIG = {
  title: "Pôle Élec",
  subtitle: "Quality Hub",
  welcome: "MOHAMMAD, bienvenue sur le dashboard de la qualité Pôle Élec",

  groups: [
    {
      name: "Outils qualité", code: "OUTILS", color: "#b5602b",
      tools: [
        { name: "PPS",             description: "Practical Problem Solving", icon: "trend-up", color: "#2e9e5b", link: "A_COMPLETER" },
        { name: "Serie Follow Up", description: "Suivi de la série",         icon: "table",    color: "#7b4fbf", link: "A_COMPLETER" },
        { name: "FOD",             description: "Foreign Object Debris",     icon: "ban",      color: "#d64545", link: "A_COMPLETER" },
        { name: "Alert Quality",   description: "Alertes qualité",           icon: "alert",    color: "#c4502a", link: "A_COMPLETER" },
        { name: "NC Dashboard",    description: "Tableau de bord des NC",    icon: "bars",     color: "#1f8f8a", link: "A_COMPLETER" },
        { name: "NC Writing",      description: "Rédaction des NC",          icon: "pen",      color: "#2b7fb0", link: "A_COMPLETER" },
        // third row of the current hub (hidden behind the scroll): name, icon and link to fill in
        { name: "À compléter",     description: "",                          icon: "link",     color: "#8592a5", link: "A_COMPLETER" },
        { name: "À compléter",     description: "",                          icon: "link",     color: "#8592a5", link: "A_COMPLETER" }
      ]
    },
    {
      name: "QCM", code: "QCM", color: "#2c4f8c",
      tools: [
        { name: "NC Eradication",  description: "Éradication des NC",        icon: "trend-down", color: "#2c4f8c", link: "A_COMPLETER" }
      ]
    },
    {
      name: "QA Management", code: "QA", color: "#2c6ad3",
      tools: [
        // one line per tile of the "QA Managment" tab of the current hub
        { name: "À compléter",     description: "",                          icon: "shield",   color: "#8592a5", link: "A_COMPLETER" }
      ]
    }
  ]
};
