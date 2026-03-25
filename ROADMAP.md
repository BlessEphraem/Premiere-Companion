# 🗺️ Roadmap - Premiere Companion

I'm bad in english, so sorry ! This note is made for me ;)

---

## 🚧 Problems
- [ ] **Missing Undo Grouping:** Actuellement, si on fait une action comme ajouter un effet a plusieurs clip, il faut
appuyé plusieurs fois sur la touche 'Undo' pour supprimer une a une, chaque action. Trouvé une solution a ça.
Voir dans 'types.d.ts' -v
    Inside `Project` -> `executeTransaction(callback: (compoundAction: CompoundAction) => void, undoString?: string): boolean`
    Inside `CompoundAction` -> `addAction(action: Action): boolean`
Voir dans 'bridge.js' -v
```js
function commitActions(project, undoLabel, actions) {
  var validActions = [];
  for (var index = 0; index < actions.length; index++) {
    if (actions[index]) validActions.push(actions[index]);
  }
  if (validActions.length === 0) return false;
  
  // Undo Grouping :
  return Boolean(project.executeTransaction(function (compoundAction) {
    for (var actionIndex = 0; actionIndex < validActions.length; actionIndex++) {
      compoundAction.addAction(validActions[actionIndex]);
    }
  }, undoLabel));
}
```
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
- [ ] **New [COMMAND] labelTag:** Celui-ci doit être visible sur la page principale et permet d'afficher des commande native a premiere pro.
Par contre pour en ajouter, il faut accédé a une nouvelle page 'User Commands'
Celle-ci permet de créer des COMPOSITIONS de commandes. On ne permet pas de faire du code pour le moment, juste d'utilisé les commandes
présente pour pouvoir créer des enchainement de commandes.
Exemple de commandes :

Clip/Motion
. Position
· Scale
. Rotation
. Anchor Point
. Anti-flicker Filter
. Opacity
. Fill Frame
. Blend Mode
. Volume
. Remove/Add/Edit (Be more complexe than premiere, can remove 'Transitions', Reset a motion value,
                    edit a specific attribute, and if i can, edit a specific attribute OF AN effect)
Clip/Time
. Speed
. Reverse
. Duration

Monitor
. Copy Frame to Clipboard

Timeline
. New Item
. Open Sequence
. Duplicate and Increment
. Add Marker (to Sequence / Selection / Clip)
. Target Video/Audio Tracks
. Mute Video/Audio Tracks
. Lock Video/Audio Tracks
. Sync Lock Video/Audio Tracks
. Match Frame to Source Sequence
. Reverse Match Frame
. Move Playhead
Timeline/Selection 
. Select Clip Above/Below
. Extend Selection
. Select All Clips ->  Disabled `or` After/Before Playhead
. Invert Selection
Timeline/Clip
. Rename
. Label
. Paste Clip
. Nest (both 'Individual' or 'All Selected')
. Trim (In/Out Point to Playhead)
. Move (Clip Start/End to Playhead)
. Show Clip Keyframes

Export
. Export Media
. Export Selected Clips
. Export Frame
. Export Frames at Markers

Project
. Increment and Save
. Change Workspace
. Execute Script

Preferences
. Display Color Management
. Snap playhead in Timeline
. Selection Follows Playhead
. Linked Selection
. Show Rulers/Guides/Transparency Grid
. Snap in Program Monitor

Special
. Undo

- [ ] **Transitions audio:** Je les ai oublié car je les utilise pas (étant donné que premiere pro en propose que 3) mais ça peut être important.
- [ ] **Une case a ajouter au coté des effet et preset dans la liste**: Uniquement sur la page principal, on peut ignoré en cochant un élément, le rendant invisible durant la recherche d'effet.

## 💡 Ideas
- [ ] Possibilité d'exporter/importer ses configurations `Data/` facilement via l'UI.

---

## ✅ Done
- [X] Panneau "Hotkeys" pour permettre des executions rapide basé sur des raccourcis clavier (ex: "Ctrl+1" pour "Appliquer Preset01")
- [X] L'utilisateur peut gêner le déplacement de la souris lors de l'application des presets

////