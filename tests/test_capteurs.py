
import json
import urllib.request

URL = "http://127.0.0.1:5000/api/sensors"

tests = [
    {
        "nom": "ZONE LIBRE",
        "distances": {"front": 100, "left": 100, "right": 100}
    },
    {
        "nom": "ATTENTION",
        "distances": {"front": 40, "left": 100, "right": 100}
    },
    {
        "nom": "OBSTACLE PROCHE",
        "distances": {"front": 100, "left": 100, "right": 15}
    }
]

for test in tests:

    donnees = json.dumps(test["distances"]).encode("utf-8")

    requete = urllib.request.Request(
        URL,
        data=donnees,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(requete) as reponse:
        print("\nTest :", test["nom"])
        print("Capteurs mis à jour :", reponse.status)

    with urllib.request.urlopen(
        "http://127.0.0.1:5000/api/obstacles"
    ) as reponse:

        resultat = json.loads(reponse.read().decode("utf-8"))

        print("Décision du système :", resultat["decision"])

print("\nTests terminés.")
