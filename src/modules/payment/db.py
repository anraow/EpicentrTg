import sqlite3
import datetime
import pytz

locCon = sqlite3.connect('local.db', check_same_thread=False)
cur = locCon.cursor()


# adds transaction to the transactions table.
def add_v_transaction(source, hash, value, comment):
    cur.execute("INSERT INTO transactions (source, hash, value, comment) VALUES (?, ?, ?, ?)",
                (source, hash, value, comment))
    locCon.commit()


# function checks whether the found transaction is in the database or not.
def check_transaction(hash):
    cur.execute(f"SELECT hash FROM transactions WHERE hash = '{hash}'")
    result = cur.fetchone()
    if result:
        return True
    return False


# checks if the user is in the database and adds him if not.
def check_user(user_id, username, first_name):
    cur.execute(f"SELECT id FROM users WHERE id = '{user_id}'")
    result = cur.fetchone()

    if not result:
        cur.execute("INSERT INTO users (id, username, first_name) VALUES (?, ?, ?)",
                    (user_id, username, first_name))
        locCon.commit()
        return False
    return True


# function checks if the user has an associated wallet. If there is, then returns it. If not, then adds.
def v_wallet(user_id, wallet):
    cur.execute(f"SELECT wallet FROM users WHERE id = '{user_id}'")
    result = cur.fetchone()
    if result[0] == "none":
        cur.execute(
            f"UPDATE users SET wallet = '{wallet}' WHERE id = '{user_id}'")
        locCon.commit()
        return True
    else:
        return result[0]


# simply returns the user's wallet.
def get_user_wallet(user_id):
    cur.execute(f"SELECT wallet FROM users WHERE id = '{user_id}'")
    result = cur.fetchone()
    return result[0]


# returns the user's payments list. This function checks if the user has a wallet.
# If he has, then it returns the payment list.
def get_user_payments(user_id):
    wallet = get_user_wallet(user_id)

    if wallet == "none":
        return "You have no wallet"
    else:
        cur.execute(f"SELECT * FROM transactions WHERE source = '{wallet}'")
        result = cur.fetchall()
        tdict = {}
        tlist = []
        try:
            for transaction in result:
                tdict = {
                    "value": transaction[2],
                    "comment": transaction[3],
                }
                tlist.append(tdict)
            return tlist
        except:
            return False
