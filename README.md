# EducPro


## Prérequis

- <a href="https://www.docker.com/products/docker-desktop/" target="_blank">Docker Desktop</a> installé et lancé


## Installation

```bash
git clone https://github.com/ton-repo/EducPro.git
cd EducPro
```

Copie les fichiers d'environnement et remplis les variables :

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
cp .env.example .env
```


## Lancer le projet

```bash
docker compose up -d --build
```

## Pour les tests, veuillez démarrer le script python qui permet de remplir les tables de la base de données avec des données de test

```bash
pip install -r backend/requirements.txt
pip install python-dotenv bcrypt mysql-connector-python
python seed.py
```


## Accéder au projet

<table>
  <tr>
    <th>Service</th>
    <th>URL</th>
  </tr>
  <tr>
    <td>🌐 Plateforme Éducative (Admin/Prof/Élève)</td>
    <td><a href="http://localhost:3000" target="_blank">http://localhost:3000</a></td>
  </tr>
  <tr>
    <td>🐍 Backend API</td>
    <td><a href="http://localhost:5000" target="_blank">http://localhost:5000</a></td>
  </tr>
  <tr>
    <td>🗄️ MySQL</td>
    <td>localhost:3306</td>
  </tr>
</table>


## Arrêter le projet

```bash
docker compose down
```
