---
name: auth-garmin
description: Use when Garmin authentication fails, first-time setup is required, or stored tokens must be refreshed.
---

# auth-garmin

## Quand l'utiliser

- Premier setup Garmin Connect
- `sync-garmin` / `export-plan-garmin` échoue sur un problème de token
- L'utilisateur veut forcer une reconnexion

## Commande

```bash
python -m garmin_coach.auth_garmin \
  [--tokens-dir DIR] \
  [--email EMAIL] \
  [--password PASSWORD] \
  [--force-login]
```

## Contrat réel

- Sans `--force-login`, le script essaie d'abord de réutiliser les tokens existants.
- Avec `--force-login`, il force un login complet.
- Si `--force-login` est présent sans `--email` / `--password`, le script demande les identifiants en interactif.

## Sortie typique

```json
{
  "status": "success",
  "tokens_path": "data/tokens",
  "warnings": []
}
```

## Échec typique

```json
{
  "status": "failed",
  "errors": ["Email and password required for initial login."]
}
```
