
from flask import Flask, render_template, jsonify, request
from datetime import datetime
from threading import Lock

app = Flask(__name__)

# ==========================================
# VARIABLES DU ROBOT
# ==========================================

lock = Lock()

robot = {
    "status": "EN ATTENTE",
    "connected": False,
    "esp32_connected": False,
    "emergency_stop": False,
    "destination": None,
    "last_update": None
}

sensors = {
    "front": 100,
    "left": 100,
    "right": 100
}

# Commande disponible pour l'ESP32
motor_command = {
    "action": "ARRET",
    "speed": 0,
    "updated_at": None
}


def update_time():
    return datetime.now().isoformat(timespec="seconds")


# ==========================================
# ANALYSE DES OBSTACLES
# ==========================================

def analyze_obstacles():

    results = {}

    for name, distance in sensors.items():

        if distance < 20:
            state = "OBSTACLE PROCHE"

        elif distance <= 50:
            state = "ATTENTION"

        else:
            state = "ZONE LIBRE"

        results[name] = {
            "distance": distance,
            "etat": state
        }

    if any(value["distance"] < 20 for value in results.values()):
        decision = "ARRET"

    elif any(value["distance"] <= 50 for value in results.values()):
        decision = "RALENTIR"

    else:
        decision = "CONTINUER"

    return {
        "capteurs": results,
        "decision": decision
    }


# ==========================================
# NAVIGATION INTELLIGENTE
# ==========================================

def navigate_robot():

    if robot["emergency_stop"]:
        return {
            "action": "ARRET",
            "reason": "Arret d'urgence actif"
        }

    front = sensors["front"]
    left = sensors["left"]
    right = sensors["right"]

    if front > 50:
        return {
            "action": "AVANCER",
            "reason": "Route degagee devant"
        }

    elif front >= 20:
        return {
            "action": "RALENTIR",
            "reason": "Obstacle detecte devant"
        }

    elif left < 20 and right < 20:
        return {
            "action": "ARRET",
            "reason": "Les deux directions laterales sont bloquees"
        }

    elif left >= right and left >= 20:
        return {
            "action": "TOURNER_GAUCHE",
            "reason": "La gauche est la direction la plus degagee"
        }

    elif right >= 20:
        return {
            "action": "TOURNER_DROITE",
            "reason": "La droite est la direction la plus degagee"
        }

    return {
        "action": "ARRET",
        "reason": "Aucune direction disponible"
    }


# ==========================================
# MISE A JOUR DE LA COMMANDE MOTEUR
# ==========================================

def update_motor_command():

    navigation = navigate_robot()

    action = navigation["action"]

    # Vitesse indicative, à calibrer avec les moteurs
    speeds = {
        "AVANCER": 150,
        "RALENTIR": 80,
        "TOURNER_GAUCHE": 100,
        "TOURNER_DROITE": 100,
        "ARRET": 0
    }

    motor_command["action"] = action
    motor_command["speed"] = speeds.get(action, 0)
    motor_command["updated_at"] = update_time()

    return motor_command.copy()


# ==========================================
# PAGE PRINCIPALE
# ==========================================

@app.route("/")
def index():
    return render_template("index.html")


# ==========================================
# ETAT DU ROBOT
# ==========================================

@app.route("/api/status", methods=["GET"])
def get_status():

    return jsonify({
        **robot,
        "connected": robot["esp32_connected"]
    })


# ==========================================
# CAPTEURS
# ==========================================

@app.route("/api/sensors", methods=["GET"])
def get_sensors():

    with lock:
        return jsonify(sensors.copy())


@app.route("/api/sensors", methods=["POST"])
def update_sensors():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Donnees JSON invalides"
        }), 400

    with lock:

        for name in ["front", "left", "right"]:

            if name in data:

                try:
                    value = float(data[name])

                    if not 0 <= value <= 400:
                        raise ValueError()

                    sensors[name] = value

                except (ValueError, TypeError):
                    return jsonify({
                        "success": False,
                        "message": f"Valeur invalide pour {name}"
                    }), 400

        robot["last_update"] = update_time()

        update_motor_command()

    return jsonify({
        "success": True,
        "message": "Capteurs mis a jour",
        "sensors": sensors.copy()
    })


# ==========================================
# DETECTION DES OBSTACLES
# ==========================================

@app.route("/api/obstacles", methods=["GET"])
def get_obstacles():

    with lock:
        return jsonify(analyze_obstacles())


# ==========================================
# NAVIGATION
# ==========================================

@app.route("/api/navigation", methods=["GET"])
def get_navigation():

    with lock:

        navigation = navigate_robot()

        return jsonify({
            "distances": sensors.copy(),
            "emergency_stop": robot["emergency_stop"],
            "navigation": navigation
        })


# ==========================================
# COMMANDES MOTEURS
# ==========================================

@app.route("/api/motor-command", methods=["GET"])
def get_motor_command():

    with lock:

        command = update_motor_command()

        return jsonify({
            "success": True,
            "command": command
        })


# ==========================================
# RECEPTION DES COMMANDES ESP32
# ==========================================

@app.route("/api/esp32/command", methods=["GET"])
def esp32_get_command():

    with lock:

        robot["esp32_connected"] = True

        command = update_motor_command()

        return jsonify({
            "success": True,
            "command": command
        })


# ==========================================
# RECEPTION DES MESURES ESP32
# ==========================================

@app.route("/api/esp32/sensors", methods=["POST"])
def esp32_send_sensors():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Donnees JSON invalides"
        }), 400

    with lock:

        for name in ["front", "left", "right"]:

            if name in data:

                try:
                    value = float(data[name])

                    if not 0 <= value <= 400:
                        raise ValueError()

                    sensors[name] = value

                except (ValueError, TypeError):
                    return jsonify({
                        "success": False,
                        "message": f"Valeur invalide pour {name}"
                    }), 400

        robot["esp32_connected"] = True
        robot["last_update"] = update_time()

        update_motor_command()

    return jsonify({
        "success": True,
        "message": "Mesures ESP32 recues"
    })


# ==========================================
# LIVRAISONS
# ==========================================

@app.route("/api/delivery", methods=["POST"])
def create_delivery():

    data = request.get_json(silent=True) or {}

    destination = data.get("destination")

    if destination not in ["A", "B", "C"]:
        return jsonify({
            "success": False,
            "message": "Destination invalide"
        }), 400

    with lock:

        if robot["emergency_stop"]:
            return jsonify({
                "success": False,
                "message": "Commande refusee : arret d'urgence actif."
            }), 409

        robot["destination"] = destination
        robot["status"] = "MISSION EN ATTENTE"

    return jsonify({
        "success": True,
        "message": f"Mission envoyee vers le point {destination}"
    })


# ==========================================
# ARRET D'URGENCE
# ==========================================

@app.route("/api/emergency-stop", methods=["POST"])
def emergency_stop():

    with lock:

        robot["emergency_stop"] = True
        robot["status"] = "ARRET D'URGENCE"

        motor_command["action"] = "ARRET"
        motor_command["speed"] = 0
        motor_command["updated_at"] = update_time()

    return jsonify({
        "success": True,
        "message": "Arret d'urgence active"
    })


# ==========================================
# REINITIALISATION
# ==========================================

@app.route("/api/reset-emergency-stop", methods=["POST"])
def reset_emergency_stop():

    with lock:

        robot["emergency_stop"] = False
        robot["status"] = "EN ATTENTE"
        robot["destination"] = None

        update_motor_command()

    return jsonify({
        "success": True,
        "message": "Systeme reinitialise"
    })


# ==========================================
# LANCEMENT DU SERVEUR
# ==========================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
