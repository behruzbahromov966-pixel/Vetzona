from __future__ import annotations

import aiosqlite


class Database:
    def __init__(self, path: str) -> None:
        self.path = path

    async def init(self) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    full_name TEXT,
                    phone TEXT,
                    role TEXT,
                    username TEXT,
                    language_code TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS pharmacies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    address TEXT NOT NULL,
                    image_url TEXT,
                    admin_note TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS referral_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user_id INTEGER NOT NULL,
                    referral_text TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    accepted_by_doctor_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    accepted_at TEXT
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS referral_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referral_request_id INTEGER NOT NULL,
                    doctor_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(referral_request_id, doctor_id)
                )
                """
            )
            await self._migrate_users_table(db)
            await self._migrate_pharmacies_table(db)
            await db.commit()

    async def _migrate_users_table(self, db: aiosqlite.Connection) -> None:
        cursor = await db.execute("PRAGMA table_info(users)")
        rows = await cursor.fetchall()
        existing_columns = {row[1] for row in rows}

        if "phone" not in existing_columns:
            await db.execute("ALTER TABLE users ADD COLUMN phone TEXT")
        if "role" not in existing_columns:
            await db.execute("ALTER TABLE users ADD COLUMN role TEXT")
        if "full_name" not in existing_columns:
            await db.execute("ALTER TABLE users ADD COLUMN full_name TEXT")

    async def _migrate_pharmacies_table(self, db: aiosqlite.Connection) -> None:
        cursor = await db.execute("PRAGMA table_info(pharmacies)")
        rows = await cursor.fetchall()
        existing_columns = {row[1] for row in rows}

        if "image_url" not in existing_columns:
            await db.execute("ALTER TABLE pharmacies ADD COLUMN image_url TEXT")
        if "admin_note" not in existing_columns:
            await db.execute("ALTER TABLE pharmacies ADD COLUMN admin_note TEXT")

    async def touch_user(
        self, user_id: int, username: str | None, language_code: str | None
    ) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """
                INSERT INTO users(user_id, username, language_code)
                VALUES(?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username=excluded.username,
                    language_code=excluded.language_code
                """,
                (user_id, username, language_code),
            )
            await db.commit()

    async def register_user(self, user_id: int, full_name: str, phone: str, role: str) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """
                UPDATE users
                SET full_name = ?, phone = ?, role = ?
                WHERE user_id = ?
                """,
                (full_name, phone, role, user_id),
            )
            await db.commit()

    async def get_user(self, user_id: int) -> tuple | None:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                SELECT user_id, full_name, phone, role, username, language_code, created_at
                FROM users
                WHERE user_id = ?
                """,
                (user_id,),
            )
            return await cursor.fetchone()

    async def get_users(self) -> list[tuple]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                SELECT user_id, full_name, phone, role, username, language_code, created_at
                FROM users
                ORDER BY created_at DESC
                """
            )
            return await cursor.fetchall()

    async def get_users_count(self) -> int:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            row = await cursor.fetchone()
            return int(row[0]) if row else 0

    async def add_pharmacy(
        self, name: str, phone: str, address: str, image_url: str | None = None, admin_note: str | None = None
    ) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """
                INSERT INTO pharmacies(name, phone, address, image_url, admin_note)
                VALUES(?, ?, ?, ?, ?)
                """,
                (name, phone, address, image_url, admin_note),
            )
            await db.commit()

    async def remove_pharmacy(self, pharmacy_id: int) -> bool:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("DELETE FROM pharmacies WHERE id = ?", (pharmacy_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def get_pharmacies(self) -> list[tuple]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                SELECT id, name, phone, address, image_url, admin_note
                FROM pharmacies
                ORDER BY id DESC
                """
            )
            return await cursor.fetchall()

    async def get_doctors(self) -> list[tuple[int, str, str]]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                SELECT user_id, full_name, phone
                FROM users
                WHERE role = 'doctor'
                ORDER BY created_at DESC
                """
            )
            return await cursor.fetchall()

    async def create_referral_request(self, from_user_id: int, referral_text: str) -> int:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                INSERT INTO referral_requests(from_user_id, referral_text, status)
                VALUES(?, ?, 'pending')
                """,
                (from_user_id, referral_text),
            )
            await db.commit()
            return int(cursor.lastrowid)

    async def add_referral_message(self, referral_request_id: int, doctor_id: int, message_id: int) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """
                INSERT INTO referral_messages(referral_request_id, doctor_id, message_id)
                VALUES(?, ?, ?)
                ON CONFLICT(referral_request_id, doctor_id) DO UPDATE SET
                    message_id=excluded.message_id
                """,
                (referral_request_id, doctor_id, message_id),
            )
            await db.commit()

    async def get_referral_messages(self, referral_request_id: int) -> list[tuple[int, int]]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                SELECT doctor_id, message_id
                FROM referral_messages
                WHERE referral_request_id = ?
                """,
                (referral_request_id,),
            )
            return await cursor.fetchall()

    async def try_accept_referral(self, referral_request_id: int, doctor_id: int) -> bool:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                UPDATE referral_requests
                SET status = 'accepted',
                    accepted_by_doctor_id = ?,
                    accepted_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'pending'
                """,
                (doctor_id, referral_request_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def get_referral_counts_by_doctor(self) -> list[tuple[int, str | None, int]]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                SELECT rm.doctor_id, MAX(COALESCE(u.full_name, '')), COUNT(*) AS cnt
                FROM referral_messages rm
                LEFT JOIN users u ON u.user_id = rm.doctor_id
                GROUP BY rm.doctor_id
                ORDER BY cnt DESC, rm.doctor_id ASC
                """
            )
            return await cursor.fetchall()

    async def get_referral_sender_recipient_edges(self) -> list[tuple[int, int]]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                SELECT DISTINCT rr.from_user_id, rm.doctor_id
                FROM referral_messages rm
                INNER JOIN referral_requests rr ON rr.id = rm.referral_request_id
                """
            )
            return await cursor.fetchall()

    async def get_referrals_with_contacted_doctors(self, limit: int = 100) -> list[tuple]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                SELECT
                    rr.id,
                    rr.from_user_id,
                    fu.full_name,
                    fu.phone,
                    rr.referral_text,
                    rr.status,
                    rr.accepted_by_doctor_id,
                    rr.created_at,
                    rr.accepted_at,
                    GROUP_CONCAT(DISTINCT CAST(rm.doctor_id AS TEXT) || ':' || COALESCE(du.full_name, ''))
                FROM referral_requests rr
                LEFT JOIN users fu ON fu.user_id = rr.from_user_id
                LEFT JOIN referral_messages rm ON rm.referral_request_id = rr.id
                LEFT JOIN users du ON du.user_id = rm.doctor_id
                GROUP BY rr.id
                ORDER BY rr.id DESC
                LIMIT ?
                """,
                (limit,),
            )
            return await cursor.fetchall()
