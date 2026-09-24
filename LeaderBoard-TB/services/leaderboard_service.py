import httpx
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from models.user import User

EXTERNAL_API_URL = "http://192.248.144.79:6979/api/v1/leaderboard"


async def fetch_and_sync(db: Session):
    """Fetch leaderboard data from external API and upsert into SQLite."""
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.get(EXTERNAL_API_URL)
        # print(f"External API response status: {response.status_code}")
        response.raise_for_status()
        payload = response.json()
        print(f"Fetched {len(payload.get('data', []))} records from external API")

    if payload.get("error"):
        raise Exception("External API returned an error")

    records = payload.get("data", [])

    for record in records:
        existing = db.query(User).filter(User.account_id == record["account_id"]).first()
        if existing:
            existing.user_id = record["user_id"]
            existing.username = record.get("username", "")
            existing.first_name = record.get("first_name", "")
            existing.last_name = record.get("last_name", "")
            existing.balance = record["balance"]
            existing.equity = record["equity"]
            existing.current_pnl = record["current_pnl"]
            existing.rank = record["rank"]
            existing.updated_at = datetime.now(timezone.utc)
        else:
            db.add(User(
                account_id=record["account_id"],
                user_id=record["user_id"],
                username=record.get("username", ""),
                first_name=record.get("first_name", ""),
                last_name=record.get("last_name", ""),
                balance=record["balance"],
                equity=record["equity"],
                current_pnl=record["current_pnl"],
                rank=record["rank"],
            ))

    db.commit()
    print(records)
    return len(records)


def get_leaderboard(db: Session, page: int = 1, page_size: int = 10):
    """Return paginated leaderboard sorted by PnL (highest first).

    Rank is computed from this order rather than trusted from the upstream API's
    "rank" field, which can be duplicated or inconsistent for a given sync.
    """
    max_records = 40
    all_total = db.query(User).count()
    total = min(all_total, max_records)
    offset = (page - 1) * page_size
    if offset >= max_records:
        return {"total": total, "all_total": all_total, "page": page, "page_size": page_size, "total_pages": (total + page_size - 1) // page_size, "data": []}
    limit = min(page_size, max_records - offset)
    users = db.query(User).order_by(User.current_pnl.desc()).offset(offset).limit(limit).all()
    data = []
    for i, u in enumerate(users):
        d = _user_to_dict(u)
        d["rank"] = offset + i + 1
        data.append(d)
    return {
        "total": total,
        "all_total": all_total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "data": data,
    }


def get_user_rank(db: Session, user_id: int):
    """Find a specific user's rank by user_id (computed from PnL order, not the stored rank field)."""
    user = db.query(User).filter(User.user_id == user_id).first()
    print(f"Queried user_id={user_id}, found: {user}")
    if not user:
        return None
    higher = db.query(User).filter(User.current_pnl > user.current_pnl).count()
    d = _user_to_dict(user)
    d["rank"] = higher + 1
    return d


def search_user(db: Session, query: str):
    """Search user by account_id or partial first_name/username (case-insensitive).

    Rank is computed from PnL order, not the stored rank field.
    """
    def with_rank(u):
        higher = db.query(User).filter(User.current_pnl > u.current_pnl).count()
        d = _user_to_dict(u)
        d["rank"] = higher + 1
        return d

    if query.isdigit():
        user = db.query(User).filter(User.account_id == int(query)).first()
        if user:
            return [with_rank(user)]
    search_term = f"%{query}%"
    users = (
        db.query(User)
        .filter(User.first_name.ilike(search_term) | User.username.ilike(search_term))
        .order_by(User.current_pnl.desc())
        .all()
    )
    if users:
        return [with_rank(u) for u in users]
    return None


def get_all_leaderboard_data(db: Session):
    """Return all leaderboard data sorted by PnL (for export); rank is computed from this order."""
    users = db.query(User).order_by(User.current_pnl.desc()).all()
    data = []
    for i, u in enumerate(users):
        d = _user_to_dict(u)
        d["rank"] = i + 1
        data.append(d)
    return data


def get_leaderboard_data_for_range(db: Session, start_dt: datetime, end_dt: datetime):
    """Return leaderboard data with updated_at within the provided datetime range."""
    users = (
        db.query(User)
        .filter(User.updated_at >= start_dt, User.updated_at <= end_dt)
        .order_by(User.current_pnl.desc())
        .all()
    )
    return [_user_to_dict(u) for u in users]


def _user_to_dict(user: User) -> dict:
    return {
        "account_id": user.account_id,
        "balance": user.balance,
        "current_pnl": user.current_pnl,
        "equity": user.equity,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "rank": user.rank,
        "user_id": user.user_id,
        "username": user.username,
    }
