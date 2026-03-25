# 🗺️ Roadmap - Premiere Companion

I'm bad in english, so sorry ! This note is made for me ;)

---

## 🚧 Problems
- [ ] **Les presets restent sur la souris jusqu'a ce qu'on clique de nouveau:**
Actuellement, quand applique un preset, que sa sois depuis l'interface ou avec la barre de recherche, il se passe ceci :
/ Sauvegarde les positions de la souris
/ Recherche l'effet demandé, et amène la souris au position sauvegarder lors de la capture
/ Ramène a la position de dépars, et laisse l'utilisateur avec le preset sur la souris.
/ Il faut alors cliquer sur un clip ou plusieurs pré-sélectionné, pour appliquer l'effet.
J'aime personnelement cette implémentation, mais pas tout le monde.
Une coche dans les paramêtre peut être sympa ?

J'ai juste oublié de faire un BlockInput entre le début et la fin de l'application du preset.
J'doit le corrigé

## 🚧 Work In Progress
- [ ] **Refonte de X :** Amélioration des performances sur la recherche de presets.
- [ ] **Convention de nommage :** 'FxVideo', 'FxAudio', 'Transion Video', il faut une meilleur convention de nommage.
A ajouter comme paramêtre modifiable dans la configuration du theme.

## 📅 To Do
- [ ] **Transitions audio:** Je les ai oublié car je les utilise pas (étant donné que premiere pro en propose que 3) mais ça peut être important.
- [ ] **Une case a ajouter au coté des effet et preset dans la liste**: Uniquement sur la page principal, on peut ignoré en cochant un élément, le rendant invisible durant la recherche d'effet.

## 💡 Ideas
- [ ] Possibilité d'exporter/importer ses configurations `Data/` facilement via l'UI.

---

## ✅ Done
- [X] Panneau "Hotkeys" pour permettre des executions rapide basé sur des raccourcis clavier (ex: "Ctrl+1" pour "Appliquer Preset01")
- [X] L'utilisateur peut gêner le déplacement de la souris lors de l'application des presets

////