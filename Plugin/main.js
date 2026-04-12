const ppro = require("premierepro");
let ws = null;
let autoConnectTimer = null;

let intentionalDisconnect = false;

function connectWebSocket() {
    const statusText = document.getElementById("status-text");
    const statusIcon = document.getElementById("status-icon");
    const btnConnect = document.getElementById("btnConnect");
    const portInput = document.getElementById("portInput");

    // SÉCURITÉ : Tuer les clones de connexion proprement sans déclencher l'auto-reconnect
    if (ws) {
        intentionalDisconnect = true;
        ws.close();
        ws = null;
    }
    intentionalDisconnect = false; // On remet à false pour la nouvelle connexion

    statusText.innerText = "Connexion en cours...";
    statusText.style.color = "orange";
    statusIcon.innerText = "⏳";

    let port = portInput ? portInput.value : "8090";
    
    try {
        localStorage.setItem("pc_ws_port", port);
        const autoConnectCheckbox = document.getElementById("autoConnectCheckbox");
        if (autoConnectCheckbox) {
            localStorage.setItem("pc_auto_connect", autoConnectCheckbox.checked);
        }
    } catch(e) {}

    ws = new WebSocket(`ws://127.0.0.1:${port}`);

    ws.onopen = async () => {
        statusText.innerText = "Connected";
        statusText.style.color = "#55ff55";
        statusIcon.innerText = "🟢";
        if(btnConnect) {
            btnConnect.innerText = "✅ Synced";
            btnConnect.disabled = true;
        }
    };

    ws.onclose = () => {
        statusText.innerText = "Disconnected";
        statusText.style.color = "#ff5555";
        statusIcon.innerText = "🔴";
        if(btnConnect) {
            btnConnect.innerText = "❌ Press to connect WebSocket";
            btnConnect.disabled = false;
        }
        
        // Auto-reconnect logic SEULEMENT si ce n'est pas une fermeture manuelle du code
        try {
            if (!intentionalDisconnect && localStorage.getItem("pc_auto_connect") === "true") {
                statusText.innerText = "Connection...";
                statusText.style.color = "orange";
                clearTimeout(autoConnectTimer);
                autoConnectTimer = setTimeout(connectWebSocket, 3000);
            }
        } catch(e) {}
    };

    ws.onmessage = async (event) => {
        try {
            const command = JSON.parse(event.data);
            console.log("⚡ Command :", command.action, "->", command.matchName);

            if (command.action === "get_effects") {
                await syncEffects();
            }
            
            if (command.action === "get_premiere_version") {
                const uxp = require("uxp");
                ws.send(JSON.stringify({
                    action: "host_info",
                    name: uxp.host.name,
                    version: uxp.host.version
                }));
            }
            
            if (command.action === "apply_effect") {
                applyEffect(command).catch(err => {
                    console.error("Error :", err);
                });
            }

            if (command.action === "better_motion") {
                handleBetterMotion(command).catch(err => {
                    console.error("[BetterMotion] Error:", err);
                });
            }

            if (command.action === "apply_preset_no_kf") {
                applyPresetNoKf(command).catch(err => {
                    console.error("[PresetNoKf] Error:", err);
                });
            }

        } catch (err) {
            console.error("Error :", err);
        }
    };

    ws.onerror = (error) => {
        console.error("Erreur WebSocket :", error);
        if (ws && ws.readyState === 1) {
            ws.send(JSON.stringify({action: "tooltip_error", message: "Error UXP"}));
        }
    }
}

// ==========================================
// GESTION DES ACTIONS & UNDO GROUPING
// ==========================================
function isValidAction(action) {
    return action !== null && action !== undefined && typeof action === 'object';
}

function commitActions(project, undoLabel, actions) {
    const validActions = [];
    for (let i = 0; i < actions.length; i++) {
        if (isValidAction(actions[i])) {
            validActions.push(actions[i]);
        }
    }
    if (validActions.length === 0) {
        console.warn("[UndoGrouping] Aucune action valide à exécuter");
        return false;
    }
    
    console.log(`[UndoGrouping] Regroupement de ${validActions.length} actions sous "${undoLabel}"`);
    
    return Boolean(project.executeTransaction(function(compoundAction) {
        for (let actionIndex = 0; actionIndex < validActions.length; actionIndex++) {
            compoundAction.addAction(validActions[actionIndex]);
        }
    }, undoLabel));
}

// ==========================================
// MOTEUR D'APPLICATION UXP
// ==========================================
async function applyEffect(command) {
    const typeStr = command.type || "";
    
    if (!typeStr.includes("FX.V") && !typeStr.includes("FX.A") && !typeStr.includes("TR.V")) {
        if (ws && ws.readyState === 1) ws.send(JSON.stringify({action: "tooltip_error", message: "Type non supporté : " + typeStr}));
        return;
    }

    const matchName = command.matchName; 
    const isAudio = typeStr.includes("FX.A"); 
    const isTransition = typeStr.includes("TR.V");

    try {
        const project = await ppro.Project.getActiveProject();
        if (!project) throw new Error("Aucun projet actif.");
        
        const sequence = await project.getActiveSequence();
        if (!sequence) throw new Error("Aucune séquence active.");

        const selectedClips = [];
        const trackCount = isAudio ? await sequence.getAudioTrackCount() : await sequence.getVideoTrackCount();
        
        for (let i = 0; i < trackCount; i++) {
            const track = isAudio ? await sequence.getAudioTrack(i) : await sequence.getVideoTrack(i);
            const trackItems = track.getTrackItems(1, false); 
            
            for (let j = 0; j < trackItems.length; j++) {
                const item = trackItems[j];
                if (typeof item.getIsSelected === "function") {
                    const isSelected = await item.getIsSelected();
                    if (isSelected) selectedClips.push(item);
                }
            }
        }

        if (selectedClips.length === 0) {
            if (ws && ws.readyState === 1) ws.send(JSON.stringify({action: "tooltip_error", message: "Aucun clip sélectionné"}));
            return;
        }

        const actions = [];
        
        for (const clip of selectedClips) {
            let action = null;

            if (isTransition) {
                let transitionObj = null;
                if (isAudio && ppro.TransitionFactory) {
                    transitionObj = ppro.TransitionFactory.createAudioTransition(matchName);
                } else if (!isAudio && ppro.TransitionFactory) {
                    transitionObj = ppro.TransitionFactory.createVideoTransition(matchName);
                }

                if (!transitionObj) continue;

                // --- LE CORRECTIF EST ICI ---
                // On détermine les cibles de coupe
                let cutsToTarget = [];
                if (command.alignment === "start") cutsToTarget.push("start");
                else if (command.alignment === "end") cutsToTarget.push("end");
                else if (command.alignment === "both") cutsToTarget.push("start", "end");

                for (let cut of cutsToTarget) {
                    let isStart = (cut === "start");
                    let options = new ppro.AddTransitionOptions();
                    
                    // 1. Centrage de la transition sur le cut (1 = Centré)
                    if (typeof options.setTransitionAlignment === "function") options.setTransitionAlignment(1);
                    else options.transitionAlignment = 1;

                    // 2. C'est applyToStart qui dit à Premiere de choisir le DÉBUT ou la FIN du clip !
                    if (typeof options.setApplyToStart === "function") options.setApplyToStart(isStart);
                    else {
                        options.applyToStart = isStart;
                        options.isStart = isStart; // Fallback de sécurité
                    }

                    // 3. Durée de sécurité pour éviter le bug des marqueurs
                    if (ppro.TickTime && typeof ppro.TickTime.createWithSeconds === "function") {
                        let durationTick = ppro.TickTime.createWithSeconds(1);
                        if (typeof options.setDuration === "function") options.setDuration(durationTick);
                    }

                    let action = null;
                    if (isAudio && typeof clip.createAddAudioTransitionAction === "function") {
                        action = clip.createAddAudioTransitionAction(transitionObj, options);
                    } else if (!isAudio && typeof clip.createAddVideoTransitionAction === "function") {
                        action = clip.createAddVideoTransitionAction(transitionObj, options);
                    }

                    if (action) actions.push(action);
                }

            } else {
                let effectComponent = isAudio ? await ppro.AudioFilterFactory.createComponentByDisplayName(matchName, clip) : await ppro.VideoFilterFactory.createComponent(matchName);
                if (!effectComponent) continue;

                const componentChain = await clip.getComponentChain();
                if (typeof componentChain.createAppendComponentAction === "function") {
                    action = componentChain.createAppendComponentAction(effectComponent);
                }
                if (action) actions.push(action);
            }
        }

        if (actions.length === 0) throw new Error(`Impossible de formuler l'action.`);

        const success = commitActions(project, `Appliquer ${typeStr}`, actions);

        if (success) {
            console.log(`✅ ${typeStr} appliqué (${actions.length} clip(s) affected(s))`);
        } else {
            throw new Error("Transaction refusée.");
        }

    } catch (err) {
        console.error("Erreur lors de l'application :", err);
        if (ws && ws.readyState === 1) {
            ws.send(JSON.stringify({action: "tooltip_error", message: "Erreur UXP : " + err.message}));
        }
    }
}



// ==========================================
// SYNCHRONISATION DES EFFETS
// ==========================================
async function syncEffects() {
    console.log("🔄 Récupération des effets...");
    let effectsList = [];

    const vFactory = ppro.VideoFilterFactory;
    const vMatch = await vFactory.getMatchNames();
    const vDisplay = await vFactory.getDisplayNames();
    
    for (let i = 0; i < vMatch.length; i++) {
        effectsList.push({ type: "FX.V", matchName: vMatch[i], displayName: vDisplay[i] || vMatch[i] });
    }

    const aFactory = ppro.AudioFilterFactory;
    const aMatch = await aFactory.getMatchNames ? await aFactory.getMatchNames() : [];
    const aDisplay = await aFactory.getDisplayNames();
    for (let j = 0; j < aDisplay.length; j++) {
        effectsList.push({ type: "FX.A", matchName: aMatch[j] || aDisplay[j], displayName: aDisplay[j] });
    }

    const tFactory = ppro.TransitionFactory;
    if (tFactory && tFactory.getVideoTransitionMatchNames) {
        const tMatch = await tFactory.getVideoTransitionMatchNames();
        for (let k = 0; k < tMatch.length; k++) {
            let cleanName = tMatch[k].replace("PR.ADBE ", "").replace("PR.", "");
            effectsList.push({ type: "TR.V", matchName: tMatch[k], displayName: cleanName });
        }
    }

    if (ws && ws.readyState === 1) {
        const chunkSize = 200;
        for (let i = 0; i < effectsList.length; i += chunkSize) {
            const chunk = effectsList.slice(i, i + chunkSize);
            ws.send(JSON.stringify({ action: "sync_done", effects: chunk }));
            await new Promise(resolve => setTimeout(resolve, 15));
        }
    }
    console.log("✅ Synchronisation terminée !");
}

// ==========================================
// BETTER MOTION
// ==========================================

// Session state for the interactive "adjust" (mouse drag) mode
let bmSession = {
    active: false,
    prop: null,
    clips: [],
    initialValues: [],   // raw values per clip (number or {x,y})
    params: [],          // ComponentParam references per clip
    lastDeltaX: 0,
    lastDeltaY: 0,
    seqWidth: 1920,      // sequence frame width  — used to normalize position deltas
    seqHeight: 1080,     // sequence frame height — used to normalize position deltas
    live: false,         // if true, each moving event applies immediately to Premiere
    currentTime: null,   // playhead position at session start (for keyframe support)
    hasTimeVarying: false // true if any clip param is already time-varying (keyframes enabled)
};

// Unwrap the value carrier wrapper that ppro wraps values in
// (adapted from reference — handles .value nesting, point-like objects, arrays)
function bmUnwrapValue(value) {
    let current = value;
    for (let depth = 0; depth < 6; depth++) {
        if (current === null || current === undefined) return null;
        if (Array.isArray(current)) return current;
        const t = typeof current;
        if (t !== "object" && t !== "function") return current;
        if ("x" in current || "y" in current || "horizontal" in current) return current;
        if (!("value" in current)) return current;
        const next = current.value;
        if (next === current) return current;
        current = next;
    }
    return current;
}

// Parse a raw ppro value to a {x, y} point — handles array, object, string forms
function bmParsePoint(raw) {
    const v = bmUnwrapValue(raw);
    if (!v) return null;
    if (Array.isArray(v)) {
        const ax = Number(v[0]), ay = Number(v[1]);
        return (isFinite(ax) && isFinite(ay)) ? { x: ax, y: ay } : null;
    }
    if (typeof v === "object" || typeof v === "function") {
        const px = [v.x, v.X, v.horizontal, v.h].map(Number).find(isFinite);
        const py = [v.y, v.Y, v.vertical,    v.v].map(Number).find(isFinite);
        return (isFinite(px) && isFinite(py)) ? { x: px, y: py } : null;
    }
    return null;
}

// Create a ppro PointF value (tries native constructor, falls back to plain object)
function bmMakePoint(x, y) {
    if (typeof ppro.PointF === "function") {
        try { return ppro.PointF(x, y); } catch (_) {}
        try { return new ppro.PointF(x, y); } catch (_) {}
    }
    return { x, y };
}

// Read the current value of a ComponentParam
// Tries getValueAtTime (with playhead) first, then getValue / getStartValue
async function bmReadParam(param, currentTime) {
    if (currentTime && typeof param.getValueAtTime === "function") {
        try {
            const raw = await param.getValueAtTime(currentTime);
            const v = bmUnwrapValue(raw);
            if (v !== null && v !== undefined) return v;
        } catch (_) {}
    }
    const readers = ["getValue", "getStartValue"];
    for (const method of readers) {
        if (typeof param[method] !== "function") continue;
        try {
            const raw = await param[method]();
            const v = bmUnwrapValue(raw);
            if (v !== null && v !== undefined) return v;
        } catch (_) {}
    }
    return null;
}

// Compare two Premiere time objects with tolerance (handles .ticks or .seconds).
function bmTimesEqual(a, b) {
    if (!a || !b) return false;
    try {
        if (typeof a.ticks !== "undefined" && typeof b.ticks !== "undefined") {
            // ~500 ticks tolerance at 254016000 ticks/sec ≈ sub-frame precision
            return Math.abs(Number(a.ticks) - Number(b.ticks)) < 500;
        }
        if (typeof a.seconds !== "undefined" && typeof b.seconds !== "undefined") {
            return Math.abs(Number(a.seconds) - Number(b.seconds)) < 0.001;
        }
        return Number(a) === Number(b);
    } catch (_) { return false; }
}

// Standard set-value action for non-time-varying params.
// Returns an array of actions to pass to commitActions().
function bmGetSetActions(param, nextValue) {
    const actions = [];
    try {
        const keyframe = param.createKeyframe(nextValue);
        const setAction = param.createSetValueAction(keyframe, true);
        if (isValidAction(setAction)) actions.push(setAction);
    } catch (_) {}
    return actions;
}

// Apply a value to an already-time-varying param using TWO sequential transactions.
// See design notes inline.  This function is async so it can re-read isTimeVarying()
// after step 1 to confirm the disable actually took effect.
async function bmCommitTimeVarying(project, clip, param, nextValue, currentTime, label) {
    try {
        const kf = param.createKeyframe(nextValue);
        const start = await clip.getStartTime();
        const inPoint = await clip.getInPoint();
        if (start && inPoint && currentTime && typeof currentTime.subtract === "function") {
            const offset = currentTime.subtract(start);
            const localTime = offset.add(inPoint);
            kf.position = localTime;
            bmLog("bmCommitTV: Set kf.position to " + localTime.seconds);
        }
        const act = param.createAddKeyframeAction(kf);
        if (isValidAction(act)) commitActions(project, label, [act]);
    } catch(e) {
        bmLog("bmCommitTV failed: " + e);
    }
}

// Legacy wrapper used by applyPresetNoKf — no keyframe logic needed for preset application.
function bmSetAction(param, nextValue) {
    const keyframe = param.createKeyframe(nextValue);
    return param.createSetValueAction(keyframe, true);
}

// Get a param's label — tries direct property access first (ppro UXP exposes displayName
// as a plain string property, not always a method), then falls back to method calls.
async function bmGetParamLabel(param) {
    if (!param) return "";
    if (typeof param.displayName === "string" && param.displayName) return param.displayName;
    if (typeof param.getDisplayName === "function") {
        try { const n = await param.getDisplayName(); if (n) return String(n); } catch (_) {}
    }
    if (typeof param.matchName === "string" && param.matchName) return param.matchName;
    if (typeof param.getMatchName === "function") {
        try { const n = await param.getMatchName(); if (n) return String(n); } catch (_) {}
    }
    return "";
}

// Find the ComponentParam for a given property key within a clip's component chain
// prop: "scale" | "position" | "rotation" | "opacity"
async function bmFindParam(clip) {
    const prop = bmSession.prop;
    if (!clip || typeof clip.getComponentChain !== "function") return null;

    let chain;
    try { chain = await clip.getComponentChain(); } catch (_) { return null; }
    if (!chain || typeof chain.getComponentCount !== "function") return null;

    const componentHints = (prop === "opacity") ? ["opacity", "opacité", "opacite"] : ["motion", "trajectoire"];

    let paramHints = [prop];
    if (prop === "scale") paramHints.push("échelle", "echelle");
    if (prop === "opacity") paramHints.push("opacité", "opacite");

    const count = chain.getComponentCount();

    for (let ci = 0; ci < count; ci++) {
        let comp = null;
        try { comp = chain.getComponentAtIndex(ci); } catch (_) { continue; }
        if (!comp) continue;

        let compDisplay = "", compMatch = "";
        try { if (typeof comp.getDisplayName === "function") compDisplay = (await comp.getDisplayName()) || ""; } catch (_) {}
        try { if (typeof comp.getMatchName  === "function") compMatch  = (await comp.getMatchName())  || ""; } catch (_) {}
        const combinedComp = (compDisplay + " " + compMatch).toLowerCase();

        let compMatchFound = false;
        for (let hint of componentHints) {
            if (combinedComp.includes(hint)) { compMatchFound = true; break; }
        }
        if (!compMatchFound) continue;

        if (typeof comp.getParamCount !== "function" || typeof comp.getParam !== "function") continue;
        const paramCount = comp.getParamCount();

        for (let pi = 0; pi < paramCount; pi++) {
            let param = null;
            try { param = comp.getParam(pi); } catch (_) { continue; }
            if (!param) continue;

            const label = (await bmGetParamLabel(param)).toLowerCase();
            for (let hint of paramHints) {
                if (label.includes(hint)) return param;
            }
        }
    }
    return null;
}

// Get the pixel dimensions of a sequence — tries getSettings() first, then direct properties.
// Position values in the UXP API are stored normalized (0.0–1.0); dividing a pixel delta
// by these dimensions converts it to the normalized unit before applying.
async function bmGetSequenceDimensions(sequence) {
    let w = 0, h = 0;
    try {
        const settings = await sequence.getSettings();
        if (settings) {
            w = Number(settings.videoFrameWidth  ?? settings.frameWidth  ?? settings.width  ?? 0);
            h = Number(settings.videoFrameHeight ?? settings.frameHeight ?? settings.height ?? 0);
        }
    } catch (_) {}
    if (!w) try { w = Number(typeof sequence.getWidth  === "function" ? await sequence.getWidth()  : (sequence.width  ?? 0)); } catch (_) {}
    if (!h) try { h = Number(typeof sequence.getHeight === "function" ? await sequence.getHeight() : (sequence.height ?? 0)); } catch (_) {}
    return { w: w || 1920, h: h || 1080 };
}

// Get selected video clips from the active sequence (also returns sequence for getPlayerPosition)
async function bmGetVideoClips() {
    const project = await ppro.Project.getActiveProject();
    if (!project) throw new Error("No active project.");
    const sequence = await project.getActiveSequence();
    if (!sequence) throw new Error("No active sequence.");

    const clips = [];
    let trackCount = 0;
    try { trackCount = await sequence.getVideoTrackCount(); } catch (_) {}

    for (let i = 0; i < trackCount; i++) {
        let track = null;
        try { track = await sequence.getVideoTrack(i); } catch (_) { continue; }
        if (!track) continue;
        const items = track.getTrackItems(1, false);
        for (let j = 0; j < items.length; j++) {
            const item = items[j];
            if (!item || typeof item.getIsSelected !== "function") continue;
            let sel = false;
            try { sel = await item.getIsSelected(); } catch (_) {}
            // Video clips have createAddVideoTransitionAction, audio clips don't
            if (sel && typeof item.createAddVideoTransitionAction === "function") clips.push(item);
        }
    }
    return { project, sequence, clips };
}

// Compute next value given initial + delta (handles scalar and {x,y} point).
// For position: the UXP API stores values normalized (0.0–1.0), so pixel deltas
// must be divided by the sequence dimensions before adding.
function bmNextValue(initial, deltaX, deltaY, seqW, seqH) {
    if (bmSession.prop === "position") {
        const pt = (initial && typeof initial === "object") ? initial : { x: 0, y: 0 };
        const w = (seqW  > 0) ? seqW  : 1920;
        const h = (seqH  > 0) ? seqH  : 1080;
        return bmMakePoint((pt.x ?? 0) + deltaX / w, (pt.y ?? 0) + deltaY / h);
    }
    const base = isFinite(Number(initial)) ? Number(initial) : 0;
    return base + deltaX;
}

// ---- BM State Machine ----

function bmLog(msg) {
    console.log("[BetterMotion]", msg);
    if (ws && ws.readyState === 1) ws.send(JSON.stringify({ action: "log", message: "[BM] " + msg }));
}

async function bmStart(prop, live) {
    bmSession = { active: false, prop, clips: [], initialValues: [], params: [], lastDeltaX: 0, lastDeltaY: 0, seqWidth: 1920, seqHeight: 1080, live: live || false, currentTime: null, hasTimeVarying: false, isCommitting: false };
    try {
        const { project, sequence, clips } = await bmGetVideoClips();
        if (clips.length === 0) {
            if (ws && ws.readyState === 1) ws.send(JSON.stringify({ action: "tooltip_error", message: "Better Motion: No clip selected." }));
            return;
        }

        if (prop === "position") {
            const dims = await bmGetSequenceDimensions(sequence);
            bmSession.seqWidth  = dims.w;
            bmSession.seqHeight = dims.h;
        }

        let currentTime = null;
        try { currentTime = await sequence.getPlayerPosition(); } catch (_) {}
        bmSession.currentTime = currentTime;

        bmSession.clips = clips;
        for (let i = 0; i < clips.length; i++) {
            const param = await bmFindParam(clips[i]);
            if (!param) {
                bmLog(`clip[${i}] param NOT FOUND for "${prop}" — check component/param names`);
                bmSession.params.push(null);
                bmSession.initialValues.push(null);
                continue;
            }
            const val = await bmReadParam(param, currentTime);
            // For position parse to {x,y}; for others keep raw scalar
            const stored = (prop === "position") ? bmParsePoint(val) : bmUnwrapValue(val);
            bmLog(`clip[${i}] param found, initial value = ${JSON.stringify(stored)}`);
            bmSession.params.push(param);
            bmSession.initialValues.push(stored);

            // Detect time-varying params — affects live-mode behaviour
            try {
                if (typeof param.isTimeVarying === "function" && Boolean(await param.isTimeVarying())) {
                    bmSession.hasTimeVarying = true;
              // Dump param keys
              try {
                  let keys = [];
                  for (let k in param) {
                      if (typeof param[k] === 'function') keys.push(k + '()');
                      else keys.push(k);
                  }
                  bmLog('Param methods: ' + keys.join(', '));
              } catch(e) { bmLog('Param methods dump failed: ' + e); }

                }
            } catch (_) {}
        }

        bmSession.active = true;
        bmLog(`Start OK: ${prop}, ${clips.length} clip(s)`);
        // Send initial value back to Python overlay for HUD display
        const firstVal = bmSession.initialValues[0];
        if (firstVal != null && ws && ws.readyState === 1) {
            ws.send(JSON.stringify({ action: "bm_ready", prop, value: firstVal }));
        }
    } catch (err) {
        console.error("[BetterMotion] bmStart:", err);
        if (ws && ws.readyState === 1) ws.send(JSON.stringify({ action: "tooltip_error", message: "Better Motion: " + err.message }));
    }
}

async function bmCommitCurrentState(deltaX, deltaY, label) {
    try {
        const project = await ppro.Project.getActiveProject();
        const sequence = await project.getActiveSequence();
        let cti = null;
        try { cti = await sequence.getPlayerPosition(); } catch (_) {}

        const finalActions = [];

        for (let i = 0; i < bmSession.clips.length; i++) {
            const clip = bmSession.clips[i];
            const param = bmSession.params[i];
            const initial = bmSession.initialValues[i];
            if (!clip || !param || initial == null) continue;
            
            const nv = bmNextValue(initial, deltaX, deltaY, bmSession.seqWidth, bmSession.seqHeight);
            
            let isTV = false;
            try { if (typeof param.isTimeVarying === "function") isTV = Boolean(await param.isTimeVarying()); } catch (_) {}
            
            try {
                const kf = param.createKeyframe(nv);
                
                if (isTV && cti) {
                    try {
                        const start = await clip.getStartTime();
                        const inPoint = await clip.getInPoint();
                        
                        let localTime = cti.subtract(start).add(inPoint);
                        kf.position = localTime;
                        
                        const act = param.createAddKeyframeAction(kf);
                        if (isValidAction(act)) finalActions.push(act);
                    } catch(e) {}
                } else {
                    const act = param.createSetValueAction(kf, true);
                    if (isValidAction(act)) finalActions.push(act);
                }
            } catch(e) {}
        }
        if (finalActions.length > 0) commitActions(project, label, finalActions);
    } catch (err) {
        console.error("[BetterMotion] bmCommitCurrentState:", err);
    }
}

async function bmMoving(deltaX, deltaY) {
    if (!bmSession.active || bmSession.clips.length === 0) return;
    bmSession.lastDeltaX = deltaX;
    bmSession.lastDeltaY = deltaY;

    if (!bmSession.live) return;
    if (bmSession.isCommitting) return;

    bmSession.isCommitting = true;
    await bmCommitCurrentState(deltaX, deltaY, "Better Motion Live: " + bmSession.prop);
    bmSession.isCommitting = false;
}

async function bmEnd(confirm) {
    if (!bmSession.active) return;
    if (confirm && bmSession.lastDeltaX === 0 && bmSession.lastDeltaY === 0) {
        bmLog("End confirm=" + confirm + " (no delta, skipped)");
        bmSession = { active: false, prop: null, clips: [], initialValues: [], params: [], lastDeltaX: 0, lastDeltaY: 0, currentTime: null, hasTimeVarying: false, isCommitting: false };
        return;
    }

    const applyOnConfirm = confirm && !bmSession.live;

    if (applyOnConfirm) {
        await bmCommitCurrentState(bmSession.lastDeltaX, bmSession.lastDeltaY, "Better Motion: " + bmSession.prop);
    } else if (!confirm && bmSession.live) {
        // Live cancel: revert Premiere to initial values
        await bmCommitCurrentState(0, 0, "Better Motion Revert: " + bmSession.prop);
    }
    
    bmLog("End confirm=" + confirm);
    bmSession = { active: false, prop: null, clips: [], initialValues: [], params: [], lastDeltaX: 0, lastDeltaY: 0, currentTime: null, hasTimeVarying: false, isCommitting: false };
}

async function bmDirect(prop, amountX, amountY) {
    try {
        bmSession.prop = prop; // needed by bmFindParam
        const { project, sequence, clips } = await bmGetVideoClips();
        if (clips.length === 0) return;

        let seqW = 1920, seqH = 1080;
        if (prop === "position") {
            const dims = await bmGetSequenceDimensions(sequence);
            seqW = dims.w;
            seqH = dims.h;
        }

        let currentTime = null;
        try { currentTime = await sequence.getPlayerPosition(); } catch (_) {}

        const label = `Better Motion: ${prop}`;
        const nonTVActions = [];
        for (const clip of clips) {
            const param = await bmFindParam(clip);
            if (!param) continue;
            const raw = await bmReadParam(param, currentTime);
            const current = (prop === "position") ? bmParsePoint(raw) : bmUnwrapValue(raw);
            if (current === null) continue;
            const nv = bmNextValue(current, amountX, amountY, seqW, seqH);
            let isTV = false;
            try { if (typeof param.isTimeVarying === "function") isTV = Boolean(await param.isTimeVarying()); } catch (_) {}
            if (isTV && currentTime) {
                await bmCommitTimeVarying(project, clip, param, nv, currentTime, label);
            } else {
                nonTVActions.push(...bmGetSetActions(param, nv));
            }
        }
        if (nonTVActions.length > 0) commitActions(project, label, nonTVActions);
    } catch (err) {
        console.error("[BetterMotion] bmDirect:", err);
        if (ws && ws.readyState === 1) ws.send(JSON.stringify({ action: "tooltip_error", message: "Better Motion: " + err.message }));
    }
}

async function bmSet(prop, amountX, amountY) {
    try {
        bmSession.prop = prop;
        const { project, sequence, clips } = await bmGetVideoClips();
        if (clips.length === 0) return;

        let seqW = 1920, seqH = 1080;
        if (prop === "position") {
            const dims = await bmGetSequenceDimensions(sequence);
            seqW = dims.w;
            seqH = dims.h;
        }

        let currentTime = null;
        try { currentTime = await sequence.getPlayerPosition(); } catch (_) {}

        const label = `Better Motion Set: ${prop}`;
        const nonTVActions = [];
        for (const clip of clips) {
            const param = await bmFindParam(clip);
            if (!param) continue;
            let nv;
            if (prop === "position") {
                const raw = await bmReadParam(param, currentTime);
                const current = bmParsePoint(raw) || { x: 0.5, y: 0.5 };
                const w = seqW > 0 ? seqW : 1920;
                const h = seqH > 0 ? seqH : 1080;
                const nx = (amountX !== undefined && amountX !== null) ? amountX / w : current.x;
                const ny = (amountY !== undefined && amountY !== null) ? amountY / h : current.y;
                nv = bmMakePoint(nx, ny);
            } else {
                if (amountX === undefined || amountX === null) continue;
                nv = amountX;
            }
            let isTV = false;
            try { if (typeof param.isTimeVarying === "function") isTV = Boolean(await param.isTimeVarying()); } catch (_) {}
            if (isTV && currentTime) {
                await bmCommitTimeVarying(project, clip, param, nv, currentTime, label);
            } else {
                nonTVActions.push(...bmGetSetActions(param, nv));
            }
        }
        if (nonTVActions.length > 0) commitActions(project, label, nonTVActions);
    } catch (err) {
        console.error("[BetterMotion] bmSet:", err);
        if (ws && ws.readyState === 1) ws.send(JSON.stringify({ action: "tooltip_error", message: "Better Motion: " + err.message }));
    }
}

async function bmReset(prop) {
    try {
        bmSession.prop = prop; // needed by bmFindParam
        const { project, sequence, clips } = await bmGetVideoClips();
        if (clips.length === 0) return;

        let currentTime = null;
        try { currentTime = await sequence.getPlayerPosition(); } catch (_) {}

        // Default values: position is normalized (0.5 = center of any sequence)
        let resetValue;
        if (prop === "position")       resetValue = bmMakePoint(0.5, 0.5);
        else if (prop === "scale")     resetValue = 100;
        else if (prop === "rotation")  resetValue = 0;
        else if (prop === "opacity")   resetValue = 100;
        else return;

        const label = `Better Motion Reset: ${prop}`;
        const nonTVActions = [];
        for (const clip of clips) {
            const param = await bmFindParam(clip);
            if (!param) continue;
            let isTV = false;
            try { if (typeof param.isTimeVarying === "function") isTV = Boolean(await param.isTimeVarying()); } catch (_) {}
            if (isTV && currentTime) {
                await bmCommitTimeVarying(project, clip, param, resetValue, currentTime, label);
            } else {
                nonTVActions.push(...bmGetSetActions(param, resetValue));
            }
        }
        if (nonTVActions.length > 0) commitActions(project, label, nonTVActions);
    } catch (err) {
        console.error("[BetterMotion] bmReset:", err);
        if (ws && ws.readyState === 1) ws.send(JSON.stringify({ action: "tooltip_error", message: "Better Motion Reset: " + err.message }));
    }
}

async function handleBetterMotion(command) {
    const { status, prop } = command;
    if (status === "start")       await bmStart(prop, command.live || false);
    else if (status === "moving") await bmMoving(command.deltaX || 0, command.deltaY || 0);
    else if (status === "end")    await bmEnd(Boolean(command.confirm));
    else if (status === "direct") await bmDirect(prop, command.amountX || 0, command.amountY || 0);
    else if (status === "set")    await bmSet(prop, command.amountX, command.amountY);
    else if (status === "reset")  await bmReset(prop);
}

// ==========================================
// APPLY PRESET (NO KEYFRAMES — API PATH)
// ==========================================

function parseParamValue(valueStr, isPoint) {
    if (isPoint) {
        const parts = valueStr.split(':');
        if (parts.length >= 2) {
            return bmMakePoint(parseFloat(parts[0]), parseFloat(parts[1]));
        }
        return null;
    }
    const lower = valueStr.toLowerCase().trim();
    if (lower === 'true') return true;
    if (lower === 'false') return false;
    const n = parseFloat(valueStr);
    return isFinite(n) ? n : null;
}

async function applyPresetNoKf(command) {
    const { matchName, presetName, params } = command;
    if (!matchName) {
        if (ws && ws.readyState === 1) ws.send(JSON.stringify({ action: "tooltip_error", message: "Preset: missing matchName" }));
        return;
    }

    try {
        const project = await ppro.Project.getActiveProject();
        if (!project) throw new Error("No active project.");
        const sequence = await project.getActiveSequence();
        if (!sequence) throw new Error("No active sequence.");

        // Collect selected video clips
        const clips = [];
        let trackCount = 0;
        try { trackCount = await sequence.getVideoTrackCount(); } catch (_) {}
        for (let i = 0; i < trackCount; i++) {
            let track = null;
            try { track = await sequence.getVideoTrack(i); } catch (_) { continue; }
            if (!track) continue;
            const items = track.getTrackItems(1, false);
            for (let j = 0; j < items.length; j++) {
                const item = items[j];
                if (!item || typeof item.getIsSelected !== "function") continue;
                let sel = false;
                try { sel = await item.getIsSelected(); } catch (_) {}
                if (sel && typeof item.createAddVideoTransitionAction === "function") clips.push(item);
            }
        }

        if (clips.length === 0) {
            if (ws && ws.readyState === 1) ws.send(JSON.stringify({ action: "tooltip_error", message: "No clip selected" }));
            return;
        }

        // Transaction 1: append the effect component to each selected clip.
        const appendActions = [];
        for (const clip of clips) {
            let effectComp = null;
            try { effectComp = await ppro.VideoFilterFactory.createComponent(matchName); } catch (_) {}
            if (!effectComp) continue;
            const chain = await clip.getComponentChain();
            const action = chain.createAppendComponentAction(effectComp);
            if (action) appendActions.push(action);
        }

        if (appendActions.length === 0) {
            if (ws && ws.readyState === 1) ws.send(JSON.stringify({ action: "tooltip_error", message: "Cannot create component: " + matchName }));
            return;
        }

        commitActions(project, `Preset: ${presetName || matchName}`, appendActions);

        // Transaction 2: set static param values.
        // We must obtain fresh component references via getComponentAtIndex() AFTER
        // the first transaction commits — the pre-append effectComp proxy goes stale
        // once Premiere moves the component into the chain during executeTransaction.
        if (params && params.length > 0) {
            const setActions = [];
            for (const clip of clips) {
                const chain = await clip.getComponentChain();
                const compCount = chain.getComponentCount();

                // Search from the end: the newly appended component is closest to the end.
                let targetComp = null;
                for (let ci = compCount - 1; ci >= 0; ci--) {
                    let c = null;
                    try { c = chain.getComponentAtIndex(ci); } catch (_) { continue; }
                    if (!c) continue;
                    let mn = c.matchName || "";
                    if (!mn) {
                        try { if (typeof c.getMatchName === "function") mn = await c.getMatchName(); } catch (_) {}
                    }
                    if (mn === matchName) { targetComp = c; break; }
                }

                if (!targetComp) continue;

                for (const p of params) {
                    try {
                        const param = targetComp.getParam(p.param_index);
                        if (!param) continue;
                        const value = parseParamValue(p.value, p.is_point);
                        if (value === null || value === undefined) continue;
                        const action = bmSetAction(param, value);
                        if (action) setActions.push(action);
                    } catch (_) {}
                }
            }
            if (setActions.length > 0) {
                commitActions(project, `Preset params: ${presetName || matchName}`, setActions);
            }
        }

        console.log(`[PresetNoKf] ✅ Applied ${presetName || matchName} to ${appendActions.length} clip(s)`);

    } catch (err) {
        console.error("[PresetNoKf]", err);
        if (ws && ws.readyState === 1) ws.send(JSON.stringify({ action: "tooltip_error", message: "Preset error: " + err.message }));
    }
}

document.querySelector("#btnConnect").addEventListener("click", () => {
    try {
        const autoConnectCheckbox = document.getElementById("autoConnectCheckbox");
        if (autoConnectCheckbox) {
            localStorage.setItem("pc_auto_connect", autoConnectCheckbox.checked);
        }
    } catch(e) {}
    connectWebSocket();
});

document.querySelector("#autoConnectCheckbox").addEventListener("change", (e) => {
    try {
        localStorage.setItem("pc_auto_connect", e.target.checked);
    } catch(err) {}
});

window.addEventListener("DOMContentLoaded", () => {
    try {
        const savedPort = localStorage.getItem("pc_ws_port");
        if (savedPort) {
            const portInput = document.getElementById("portInput");
            if (portInput) portInput.value = savedPort;
        }

        const autoConnectFlag = localStorage.getItem("pc_auto_connect");
        if (autoConnectFlag === "true") {
            const autoConnectCheckbox = document.getElementById("autoConnectCheckbox");
            if (autoConnectCheckbox) autoConnectCheckbox.checked = true;
            connectWebSocket();
        }
    } catch(e) {}
});















