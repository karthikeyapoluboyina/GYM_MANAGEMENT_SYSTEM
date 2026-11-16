<div align="center">

# 🏋️ FitGym Management System

**A modern, full-stack web application to manage gym operations — members, trainers, plans, and attendance — from one dashboard.**

[![Live Demo](https://img.shields.io/badge/Live_Demo-Railway-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)](https://web-production-9b1b4.up.railway.app)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8+-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

[View Demo](https://web-production-9b1b4.up.railway.app) · [Report Bug](https://github.com/Pradeep007-pixel/Gym_Management_System/issues) · [Request Feature](https://github.com/Pradeep007-pixel/Gym_Management_System/issues)

</div>

---

## ✨ Overview

**FitGym Management System** helps gym owners and staff streamline daily operations. Register members, assign subscription plans, track attendance, manage trainers, and view real-time analytics — all through a clean, responsive web interface.

Built with **Flask** and **MySQL**, the app is production-ready and deployed on **Railway**.

---

## 🚀 Live Application

| | |
|---|---|
| **URL** | [https://web-production-9b1b4.up.railway.app](https://web-production-9b1b4.up.railway.app) |
| **Dashboard** | [https://web-production-9b1b4.up.railway.app/dashboard](https://web-production-9b1b4.up.railway.app/dashboard) |
| **Status** | ✅ Deployed & Running |

---

## 🎯 Features

| Module | Description |
|--------|-------------|
| 👥 **Member Management** | Register, update, search, and delete member profiles with plan assignment |
| 📋 **Subscription Plans** | Create and manage Basic, Standard, Premium, and custom membership plans |
| 🧑‍🏫 **Trainer Management** | Add trainers with specialties, contact info, and bio |
| ✅ **Attendance Tracking** | Record check-ins/check-outs with date filters and member lookup |
| 📊 **Dashboard Analytics** | View total members, trainers, daily attendance, and plan distribution |
| 🔗 **Trainer Assignments** | Assign trainers to members with start/end dates via REST API |
| 🔍 **Search & Filters** | Search members and trainers; filter attendance by date range |

---

## 🛠️ Tech Stack

```
Frontend     →  HTML5 · Bootstrap · JavaScript · Chart.js
Backend      →  Python · Flask · Gunicorn
Database     →  MySQL
Deployment   →  Railway (Web + MySQL)
```

---

## 📁 Project Structure

```
Gym_Management_System/
├── app.py                 # Flask routes & REST API
├── config.py              # Environment configuration
├── db_init.py             # Database schema & seed data
├── requirements.txt       # Python dependencies
├── Procfile               # Production start command
├── railway.toml           # Railway deployment config
├── templates/             # HTML templates (Jinja2)
│   ├── layout.html
│   ├── index.html
│   ├── dashboard.html
│   ├── members.html
│   ├── trainers.html
│   ├── plans.html
│   └── attendance.html
└── static/
    ├── css/style.css
    └── js/                # Page-specific JavaScript
```

---

## ⚙️ Local Setup

### Prerequisites

- Python 3.12+
- MySQL 8+ (or XAMPP/WAMP)
- Git

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Pradeep007-pixel/Gym_Management_System.git
cd Gym_Management_System

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux

# 4. Edit .env with your MySQL credentials
#    MYSQL_HOST=localhost
#    MYSQL_USER=root
#    MYSQL_PASSWORD=
#    MYSQL_DB=gym_management_db

# 5. Initialize the database
python db_init.py

# 6. Run the development server
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

---

## 🌐 Deployment

This project is pre-configured for [Railway](https://railway.app):

1. Fork or clone this repository to your GitHub account
2. Create a new **Railway project** → Deploy from GitHub repo
3. Add a **MySQL** service to the project
4. Link MySQL environment variables to the web service:
   - `MYSQLHOST`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE`, `MYSQLPORT`
5. Set `FLASK_DEBUG=False` on the web service
6. Generate a public domain in Railway settings

**Production start command:**
```bash
python db_init.py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

---

## 🔐 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MYSQL_HOST` / `MYSQLHOST` | Database host | `localhost` |
| `MYSQL_USER` / `MYSQLUSER` | Database user | `root` |
| `MYSQL_PASSWORD` / `MYSQLPASSWORD` | Database password | `your_password` |
| `MYSQL_DB` / `MYSQLDATABASE` | Database name | `gym_management_db` |
| `MYSQL_PORT` / `MYSQLPORT` | Database port | `3306` |
| `PORT` | Server port (auto-set on Railway) | `5000` |
| `FLASK_DEBUG` | Debug mode — set `False` in production | `False` |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/members` | List all members |
| `POST` | `/api/members` | Create a member |
| `GET/PUT/DELETE` | `/api/members/<id>` | Get, update, or delete a member |
| `GET` | `/api/trainers` | List all trainers |
| `POST` | `/api/trainers` | Create a trainer |
| `GET` | `/api/plans` | List subscription plans |
| `GET` | `/api/attendance` | List attendance records |
| `POST` | `/api/attendance` | Record check-in |
| `GET` | `/api/assignments` | List trainer assignments |

---

## 👤 Author

**Althi Pradeep Kumar**

[![GitHub](https://img.shields.io/badge/GitHub-Pradeep007--pixel-181717?style=flat-square&logo=github)](https://github.com/Pradeep007-pixel)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<div align="center">

**⭐ Star this repo if you found it useful!**

</div>
