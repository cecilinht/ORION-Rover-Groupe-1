
// ==========================================
// ORION-ROVER - DASHBOARD JAVASCRIPT
// ==========================================

const API = "";

// ==========================================
// 1. MISE A JOUR DE L'ETAT DU ROBOT
// ==========================================

async function updateRobotStatus() {
    try {
        const response = await fetch(`${API}/api/status`);
        const data = await response.json();

        document.getElementById("robot-status").textContent =
            data.status;

        document.getElementById("robot-message").textContent =
            data.emergency_stop
                ? "Arrêt d'urgence activé"
                : "Système opérationnel";

        const connection = document.getElementById("connection-status");
        const dot = document.getElementById("connection-dot");

        if (data.connected) {
            connection.textContent = "Robot connecté";
            dot.style.background = "#22c55e";
        } else {
            connection.textContent = "Robot non connecté";
            dot.style.background = "#ef4444";
        }

    } catch (error) {
        console.error("Erreur état robot :", error);
    }
}


// ==========================================
// 2. MISE A JOUR DES CAPTEURS
// ==========================================

async function updateSensors() {
    try {
        const response = await fetch(`${API}/api/sensors`);
        const data = await response.json();

        document.getElementById("front-distance").textContent =
            data.front;

        document.getElementById("left-distance").textContent =
            data.left;

        document.getElementById("right-distance").textContent =
            data.right;

    } catch (error) {
        console.error("Erreur capteurs :", error);
    }
}


// ==========================================
// 3. DETECTION DES OBSTACLES
// ==========================================

async function updateObstacles() {
    try {
        const response = await fetch(`${API}/api/obstacles`);
        const data = await response.json();

        document.getElementById("obstacle-decision").textContent =
            data.decision;

        document.getElementById("obstacle-message").textContent =
            "Analyse automatique des distances";

        document.getElementById("front-obstacle-status").textContent =
            data.capteurs.front.etat;

        document.getElementById("left-obstacle-status").textContent =
            data.capteurs.left.etat;

        document.getElementById("right-obstacle-status").textContent =
            data.capteurs.right.etat;

    } catch (error) {
        console.error("Erreur obstacles :", error);
    }
}


// ==========================================
// 4. NAVIGATION INTELLIGENTE
// ==========================================

async function updateNavigation() {
    try {
        const response = await fetch(`${API}/api/navigation`);
        const data = await response.json();

        const action = data.navigation.action;
        const reason = data.navigation.reason;

        document.getElementById("navigation-action").textContent =
            action;

        document.getElementById("navigation-reason").textContent =
            reason;

        document.getElementById("navigation-front").textContent =
            data.distances.front + " cm";

        document.getElementById("navigation-left").textContent =
            data.distances.left + " cm";

        document.getElementById("navigation-right").textContent =
            data.distances.right + " cm";

        const icon = document.getElementById("navigation-icon");

        const icons = {
            "AVANCER": "↑",
            "RALENTIR": "↓",
            "TOURNER_GAUCHE": "←",
            "TOURNER_DROITE": "→",
            "ARRET": "■"
        };

        icon.textContent = icons[action] || "◆";

        const colors = {
            "AVANCER": "#22c55e",
            "RALENTIR": "#eab308",
            "TOURNER_GAUCHE": "#3b82f6",
            "TOURNER_DROITE": "#3b82f6",
            "ARRET": "#ef4444"
        };

        icon.style.color = colors[action] || "#60a5fa";

    } catch (error) {
        console.error("Erreur navigation :", error);
    }
}


// ==========================================
// 5. ENVOYER UNE MISSION
// ==========================================

document.querySelector(".primary-button").addEventListener("click",
    async function () {

        const destination =
            document.getElementById("destination").value;

        if (!destination) {
            alert("Veuillez choisir une destination.");
            return;
        }

        try {
            const response = await fetch(`${API}/api/delivery`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    destination: destination
                })
            });

            const data = await response.json();

            if (!response.ok) {
                alert(data.message || "Mission refusée.");
                return;
            }

            alert(data.message || "Mission envoyée.");

            updateRobotStatus();

        } catch (error) {
            alert("Impossible de contacter le serveur.");
            console.error(error);
        }
    }
);


// ==========================================
// 6. ARRET D'URGENCE
// ==========================================

document.querySelector(".emergency-button").addEventListener("click",
    async function () {

        const confirmation = confirm(
            "Confirmer l'arrêt d'urgence du robot ?"
        );

        if (!confirmation) return;

        try {
            const response = await fetch(
                `${API}/api/emergency-stop`,
                { method: "POST" }
            );

            const data = await response.json();

            alert(data.message || "Arrêt d'urgence activé.");

            refreshDashboard();

        } catch (error) {
            alert("Erreur pendant l'arrêt d'urgence.");
            console.error(error);
        }
    }
);


// ==========================================
// 7. REINITIALISATION
// ==========================================

document.querySelector(".reset-button").addEventListener("click",
    async function () {

        try {
            const response = await fetch(
                `${API}/api/reset-emergency-stop`,
                { method: "POST" }
            );

            const data = await response.json();

            alert(data.message || "Système réinitialisé.");

            refreshDashboard();

        } catch (error) {
            alert("Erreur pendant la réinitialisation.");
            console.error(error);
        }
    }
);


// ==========================================
// 8. ACTUALISATION GENERALE
// ==========================================

function refreshDashboard() {
    updateRobotStatus();
    updateSensors();
    updateObstacles();
    updateNavigation();
}


// Actualisation toutes les 2 secondes
refreshDashboard();
setInterval(refreshDashboard, 2000);
