---
name: auth-garmin
description: Use when Garmin authentication fails, credentials are expired, or first-time setup is required.
---

# auth-garmin

## Quand l'utiliser

- Erreur d'authentification Garmin sur n'importe quel autre script
- Premier démarrage de l'agent (pas de token stocké)
- L'utilisateur signale que Garmin ne répond plus

## Ne pas utiliser

- En routine : l'authentification est persistée, pas besoin de re-auth à chaque session
- Si le problème vient d'autre chose (réseau, API down)

## Commande

```bash
python -m garmin_coach.auth_garmin
```

Le script est interactif : il demande les identifiants Garmin Connect (email + mot de passe) et stocke le token localement.

## Sortie

```json
{
  "status": "success",
  "authenticated": true
}
```

## Gestion d'erreur

Si l'auth échoue → demander à l'utilisateur de vérifier ses identifiants Garmin Connect.  
Ne pas relancer en boucle.
