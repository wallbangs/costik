import aiosqlite

class DB:
    async def on_startup(self):
        self.con = await aiosqlite.connect("database/user.db")
        await self.con.execute(
            "CREATE TABLE IF NOT EXISTS users(verifed TEXT, user_id BIGINT PRIMARY KEY, lang TEXT, deposit TEXT DEFAULT 'nedep', subscribed TEXT DEFAULT 'no')"
        )
        # Add subscribed column to existing table if it doesn't exist
        try:
            await self.con.execute("ALTER TABLE users ADD COLUMN subscribed TEXT DEFAULT 'no'")
            await self.con.commit()
        except:
            pass  # Column already exists
        
        await self.con.execute("CREATE TABLE IF NOT EXISTS desc(ref TEXT)")
        await self.con.execute(
            "CREATE TABLE IF NOT EXISTS userslang(iduser BIGINT PRIMARY KEY, lang TEXT)"
        )
        check = await self.con.execute("SELECT ref FROM desc")
        if not await check.fetchone():
            await self.con.execute("INSERT INTO desc(ref) VALUES('google.com')")
            await self.con.commit()


    async def register_lang(self, user_id, lang) -> str:
        try:
            query = "INSERT INTO userslang(iduser, lang) VALUES(?, ?)"
            await self.con.execute(query, (user_id, lang,))
            await self.con.commit()
        except aiosqlite.IntegrityError:
            pass

    async def get_ref(self) -> str:
        query = 'SELECT * FROM desc'
        result = await self.con.execute(query)
        row = await result.fetchone()
        if row is not None:
            return row[0]
        return None

    async def edit_ref(self, url: str) -> None:
        query = 'UPDATE desc SET ref = ? WHERE ref = ?'
        await self.con.execute(query, (url, await self.get_ref()))
        await self.con.commit()

    async def get_users_count(self) -> int:
        query = "SELECT COUNT(*) FROM users"
        result = await self.con.execute(query)
        return (await result.fetchone())[0]


    
    async def check_register(self, user_id) -> int:
        query = "SELECT COUNT(*) FROM users WHERE user_id = '{0}'".format(user_id)
        result = await self.con.execute(query)
        return (await result.fetchone())[0]
    
    async def register(self, user_id, accid, deposit="0"):
        try:
            query = "INSERT INTO users(user_id, acc_number, deposit) VALUES(?, ?, ?)"
            await self.con.execute(query, (user_id, accid, deposit))
            await self.con.commit()
        except aiosqlite.IntegrityError:
            pass



    async def get_user(self, user_id):
        query = 'SELECT * FROM users WHERE user_id = ?'
        result = await self.con.execute(query, (user_id))
        return await result.fetchone()

    async def get_user_info(self, user_id):
        query = 'SELECT * FROM users WHERE user_id = ?'
        result = await self.con.execute(query, (user_id,))
        return await result.fetchone()

    async def get_users(self):
        query = "SELECT * FROM users"
        result = await self.con.execute(query)
        return await result.fetchall()

    async def update_lang(self, user_id, language: str):
        query = "UPDATE userslang SET lang = ? WHERE iduser = ?"
        await self.con.execute(query, (language, user_id))
        await self.con.commit()

    async def get_lang(self, user_id):
        query = "SELECT lang FROM userslang WHERE iduser = ?"
        result = await self.con.execute(query, (user_id,))
        row = await result.fetchone()
        if row is not None:
            return row[0]
        return None


    async def update_deposit_status(self, user_id: int, status: str = "dep"):
        query = "UPDATE users SET deposit = ? WHERE user_id = ?"
        await self.con.execute(query, (status, user_id))
        await self.con.commit()

    async def get_deposit_status(self, user_id: int) -> str:
        query = "SELECT deposit FROM users WHERE user_id = ?"
        result = await self.con.execute(query, (user_id,))
        row = await result.fetchone()
        if row is not None:
            return row[0]
        return "nedep"

    async def get_verified_users_count(self) -> int:
        query = "SELECT COUNT(*) FROM users WHERE verifed = 'verified'"
        result = await self.con.execute(query)
        return (await result.fetchone())[0]

    async def set_verification(self, user_id: int, status: str = "verified"):
        query = "UPDATE users SET verifed = ? WHERE user_id = ?"
        await self.con.execute(query, (status, user_id))
        await self.con.commit()

    async def mark_user_registered(self, user_id: int):
        # First check if user exists, if not create them
        existing = await self.get_user_info(user_id)
        if not existing:
            query = "INSERT INTO users(user_id, verifed, deposit, subscribed) VALUES(?, ?, ?, ?)"
            await self.con.execute(query, (user_id, "reg", "nedep", "yes"))
        else:
            query = "UPDATE users SET verifed = ? WHERE user_id = ?"
            await self.con.execute(query, ("reg", user_id))
        await self.con.commit()

    async def mark_user_deposited(self, user_id: int):
        # First check if user exists, if not create them
        existing = await self.get_user_info(user_id)
        if not existing:
            query = "INSERT INTO users(user_id, verifed, deposit, subscribed) VALUES(?, ?, ?, ?)"
            await self.con.execute(query, (user_id, "reg", "dep", "yes"))
        else:
            query = "UPDATE users SET deposit = ? WHERE user_id = ?"
            await self.con.execute(query, ("dep", user_id))
        await self.con.commit()

    async def delete_user(self, user_id: int):
        query = "DELETE FROM users WHERE user_id = ?"
        await self.con.execute(query, (user_id,))
        # Also delete from userslang table
        query2 = "DELETE FROM userslang WHERE iduser = ?"
        await self.con.execute(query2, (user_id,))
        await self.con.commit()

    async def set_subscription_status(self, user_id: int, status: str = "yes"):
        # First check if user exists, if not create them
        existing = await self.get_user_info(user_id)
        if not existing:
            query = "INSERT INTO users(user_id, subscribed) VALUES(?, ?)"
            await self.con.execute(query, (user_id, status))
        else:
            query = "UPDATE users SET subscribed = ? WHERE user_id = ?"
            await self.con.execute(query, (status, user_id))
        await self.con.commit()

    async def get_subscription_status(self, user_id: int) -> str:
        query = "SELECT subscribed FROM users WHERE user_id = ?"
        result = await self.con.execute(query, (user_id,))
        row = await result.fetchone()
        if row is not None:
            return row[0]
        return "no"

DataBase = DB()