# EducPro

## Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et lancé


## Installation

```bash
git clone https://github.com/ton-repo/EducPro.git
cd EducPro
```

Copie les fichiers d'environnement et remplis les variables :

```bash
cp backend/.env.example backend/.env
```

## Lancer le projet

```bash
docker compose up -d --build
```

## Accéder au projet

<table>
  <tr>
    <th>Service</th>
    <th>URL</th>
  </tr>
  <tr>
    <td>⚛️ Frontend</td>
    <td><a href="http://localhost:3000">http://localhost:3000</a></td>
  </tr>
  <tr>
    <td>🛠️ Admin</td>
    <td><a href="http://localhost:3001">http://localhost:3001</a></td>
  </tr>
  <tr>
    <td>🐍 Backend API</td>
    <td><a href="http://localhost:5000">http://localhost:5000</a></td>
  </tr>
  <tr>
    <td>🗄️ MySQL</td>
    <td><a href="http://localhost:3306">http://localhost:3306</a></td>
  </tr>
</table>

## Arrêter le projet

```bash
docker compose down
```
