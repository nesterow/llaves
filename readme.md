# llaves

Simple tools for encrypting secrets and running setup tasks.
Mostly used in order to push secrets to docker swarm or manually deploy docker-compose.

Config files:

- `.llaves` - to be gitignored, text passphrase
- `.llaves.yaml` - to be gitignored, secrets
- `entrega.yaml` - run tasks with decrypted data

Using variables:

Secrets are converted to the env variables using following  template `PRIVATE__{secretName}`
