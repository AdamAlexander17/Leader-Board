# Trade Bazaar — Leaderboard

A real-time trading leaderboard application built with **FastAPI**, **SQLite**, and a fully custom dark-themed HTML/CSS/JS frontend.

---

## Features

- **Live Leaderboard** — Displays the top 100 traders ranked by performance
- **Paginated Results** — Configurable page size (up to 100 entries per page)
- **Search** — Find any trader by Account ID or Username
- **Rank Lookup** — Query any user's rank directly by their User ID
- **Excel Export** — Download the full leaderboard as a styled `.xlsx` file
- **Persistent Storage** — SQLite database via SQLAlchemy ORM
- **External Sync Ready** — Architecture supports periodic syncing from an external trading API
- **Responsive UI** — Sticky navbar, dark theme (`#0a0a0a`), neon-green (`#b8ff00`) accents

---

## Tech Stack

| Layer      | Technology                          |
|------------|--------------------------------------|
| Backend    | Python 3.11+, FastAPI, Uvicorn       |
| Database   | SQLite + SQLAlchemy                  |
| Frontend   | Vanilla HTML / CSS / JavaScript      |
| Export     | openpyxl                             |
| HTTP Client| httpx                                |

---

## Project Structure

```
leaderboard_project/
├── main.py                          # FastAPI app entry point & lifespan
├── requirements.txt                 # Python dependencies
├── controllers/
│   └── leaderboard_controller.py   # Route handlers (API endpoints)
├── db/
│   └── database.py                  # SQLAlchemy engine & session setup
├── models/
│   └── user.py                      # User / leaderboard ORM model
├── services/
│   └── leaderboard_service.py       # Business logic & DB queries
└── static/
    └── index.html                   # Frontend SPA
```

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/AdamAlexander17/Leader-Board.git
cd Leader-Board/leaderboard_project

# 2. (Optional) Create and activate a virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Running the Server

```bash
uvicorn main:app --reload
```

The app will be available at **http://127.0.0.1:8000**

---

## API Reference

| Method | Endpoint             | Description                                    |
|--------|----------------------|------------------------------------------------|
| `GET`  | `/leaderboard`       | Paginated top-100 leaderboard                  |
| `GET`  | `/rank/{user_id}`    | Get a specific user's rank by User ID          |
| `GET`  | `/search?q=`         | Search by Account ID or Username               |
| `GET`  | `/export-excel`      | Download today's leaderboard as `.xlsx`        |
| `POST` | `/sync`              | Manual sync (disabled — returns 503)           |

### Example Requests

```bash
# Get page 1 of the leaderboard (50 per page)
GET /leaderboard?page=1&page_size=50

# Look up a user's rank
GET /rank/12345

# Search by username or account ID
GET /search?q=alex
GET /search?q=100042
```

### Example Response — `/leaderboard`

```json
{
  "total": 100,
  "all_total": 342,
  "page": 1,
  "page_size": 50,
  "total_pages": 2,
  "data": [
    {
      "rank": 1,
      "account_id": 100001,
      "user_id": 5001,
      "username": "toptrader",
      "first_name": "Adam",
      "last_name": "Alexander",
      "balance": 15000.00,
      "equity": 16200.00,
      "current_pnl": 1200.00
    }
  ]
}
```

---

## Database Schema

**Table:** `leaderboard`

| Column       | Type     | Description                        |
|--------------|----------|------------------------------------|
| `id`         | Integer  | Primary key (auto-increment)       |
| `account_id` | Integer  | Unique trading account identifier  |
| `user_id`    | Integer  | User identifier                    |
| `username`   | String   | Display username                   |
| `first_name` | String   | Trader's first name                |
| `last_name`  | String   | Trader's last name                 |
| `balance`    | Float    | Account balance                    |
| `equity`     | Float    | Account equity                     |
| `current_pnl`| Float    | Current profit & loss              |
| `rank`       | Integer  | Leaderboard rank                   |
| `updated_at` | DateTime | Last updated timestamp (UTC)       |

---

## Frontend

The frontend is a single-page application served from `/static/index.html`.

- Dark background (`#0a0a0a`) with neon-green (`#b8ff00`) highlights
- Sticky top navbar with Trade Bazaar branding
- Paginated table auto-fetches from `/leaderboard`
- Search bar queries `/search`
- Excel download button calls `/export-excel`

---

## License

This project is for internal / demonstration purposes.

---

> Built with FastAPI · SQLAlchemy · openpyxl · Vanilla JS
