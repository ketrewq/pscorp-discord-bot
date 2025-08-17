import sqlite3
from datetime import datetime
import json
import os

def _load_json(path):
    with open(path, 'rt', encoding='UTF8') as f:
        return json.load(f)

def _read_lines(path):
    with open(path, encoding='UTF8') as f:
        return [line.strip() for line in f.read().splitlines() if line.strip()]

def ensure_schema():
    conn, cur = get_conn()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        points INTEGER
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS radiation (
        ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        exposure INTEGER,
        hazmat INTEGER
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS board_tables (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        message_id TEXT,
        created_time INTEGER,
        page_number INTEGER,
        last_usernumber INTEGER
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS count (
        ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        clean INTEGER,
        search INTEGER,
        gamble INTEGER,
        video INTEGER
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS characters_meta (
        char_id TEXT PRIMARY KEY,
        name TEXT,
        emoji TEXT,
        owner_id TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS radiation_texts (
        ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        bucket TEXT,
        text TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS secret_rooms (
        password TEXT PRIMARY KEY,
        name TEXT,
        description TEXT
    )
    """)
    conn.commit()

def bootstrap_static_data():
    # migrate json to sqlite if empty
    conn, cur = get_conn()
    cur.execute("SELECT COUNT(*) FROM characters_meta")
    empty_chars = cur.fetchone()[0] == 0
    if empty_chars:
        owners_path = os.path.join(os.getcwd(), 'owners.json')
        characters_path = os.path.join(os.getcwd(), 'characters.json')
        emoji_path = os.path.join(os.getcwd(), 'emoji.json')
        if os.path.exists(owners_path) and os.path.exists(characters_path) and os.path.exists(emoji_path):
            owners = _load_json(owners_path)
            charnames = _load_json(characters_path)
            emojis = _load_json(emoji_path)
            rows = []
            for owner_id, data in owners.items():
                for c in data.get('characters', []):
                    cid = c.get('id')
                    rows.append((cid, charnames.get(cid, c.get('name', '')), emojis.get(cid, c.get('emoji', '')), owner_id))
            cur.executemany("INSERT OR REPLACE INTO characters_meta(char_id, name, emoji, owner_id) VALUES(?,?,?,?)", rows)
            conn.commit()

    cur.execute("SELECT COUNT(*) FROM radiation_texts")
    empty_texts = cur.fetchone()[0] == 0
    if empty_texts:
        base = os.path.join(os.getcwd(), 'items')
        files = {
            'secret': 'secrets.txt',
            'ten': 'ten.txt',
            'twentyfive': 'twentyfive.txt',
            'fifty': 'fifty.txt',
            'seventyfive': 'seventyfive.txt',
            'hundred': 'hundred.txt',
        }
        rows = []
        for bucket, fname in files.items():
            path = os.path.join(base, fname)
            if os.path.exists(path):
                for line in _read_lines(path):
                    rows.append((bucket, line))
        if rows:
            cur.executemany("INSERT INTO radiation_texts(bucket, text) VALUES(?,?)", rows)
            conn.commit()

    # optional secrets mapping
    secrets_path = os.path.join(os.getcwd(), 'secrets.json')
    if os.path.exists(secrets_path):
        cur.execute("SELECT COUNT(*) FROM secret_rooms")
        if cur.fetchone()[0] == 0:
            secrets = _load_json(secrets_path)
            rows = []
            for pwd, val in secrets.items():
                rows.append((pwd, val.get('name', ''), val.get('description', '')))
            if rows:
                cur.executemany("INSERT OR REPLACE INTO secret_rooms(password, name, description) VALUES(?,?,?)", rows)
                conn.commit()

ensure_schema()
bootstrap_static_data()

def _all_character_ids():
    conn, cur = get_conn()
    cur.execute("SELECT char_id FROM characters_meta")
    return [r[0] for r in cur.fetchall()]

def _owner_characters(owner_id):
    conn, cur = get_conn()
    t = (str(owner_id),)
    cur.execute("SELECT char_id, name, emoji FROM characters_meta WHERE owner_id = ? ORDER BY rowid", t)
    rows = cur.fetchall()
    return [{'id': r[0], 'name': r[1], 'emoji': r[2]} for r in rows]

def character_name(char_id):
    conn, cur = get_conn()
    t = (char_id,)
    cur.execute("SELECT name FROM characters_meta WHERE char_id = ?", t)
    r = cur.fetchone()
    return r[0] if r else ''

def character_emoji(char_id):
    conn, cur = get_conn()
    t = (char_id,)
    cur.execute("SELECT emoji FROM characters_meta WHERE char_id = ?", t)
    r = cur.fetchone()
    return r[0] if r else ''

def random_text(bucket):
    conn, cur = get_conn()
    t = (bucket,)
    cur.execute("SELECT text FROM radiation_texts WHERE bucket = ? ORDER BY RANDOM() LIMIT 1", t)
    r = cur.fetchone()
    return r[0] if r else ''

def secret_room(password):
    conn, cur = get_conn()
    t = (password,)
    cur.execute("SELECT name, description FROM secret_rooms WHERE password = ?", t)
    r = cur.fetchone()
    if not r:
        return None
    return {'name': r[0], 'description': r[1]}


def check_character(username):
    conn, cur = get_conn()
    t = (username,)
    cur.execute("SELECT COUNT(*) FROM characters_meta WHERE char_id = ?", t)
    return cur.fetchone()[0] > 0

def get_conn():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    return conn, cur

def check_count_user(username_id):
    t = (username_id, )
    conn, cur = get_conn()
    cur.execute("SELECT COUNT(*) FROM count WHERE username = ?",t)
    users = cur.fetchall()
    if(users[0][0] == 0):
        return False
    else:
        return True

def add_count_user(username_id):
    conn, cur = get_conn()
    t = (username_id, 0, 0, 0, 0)
    cur.execute("INSERT INTO count(username, clean, search, gamble, video) VALUES(?,?,?,?,?)", t)
    conn.commit()

def add_count(username_id, command):
    conn, cur = get_conn()
    t = (username_id, )
    if command == 1:
        cur.execute("UPDATE count SET clean = clean + 1 WHERE username = ?", t)
    elif command == 2:
        cur.execute("UPDATE count SET search = search + 1 WHERE username = ?", t)
    elif command == 3:
        cur.execute("UPDATE count SET gamble = gamble + 1 WHERE username = ?", t)
    elif command == 4:
        cur.execute("UPDATE count SET video = video + 1 WHERE username = ?", t)
    else:
        return 
    conn.commit()

def remove_count(username_id, command):
    conn, cur = get_conn()
    t = (username_id, )
    if command == 1:
        cur.execute("UPDATE count SET clean = clean - 1 WHERE username = ?", t)
    elif command == 2:
        cur.execute("UPDATE count SET search = search - 1 WHERE username = ?", t)
    elif command == 3:
        cur.execute("UPDATE count SET gamble = gamble - 1 WHERE username = ?", t)
    elif command == 4:
        cur.execute("UPDATE count SET video = video - 1 WHERE username = ?", t)
    else:
        return 
    conn.commit()

def get_user_count(username_id):
    conn, cur = get_conn()
    t = (username_id, )
    cur.execute("SELECT * FROM count WHERE username = ?", t)
    data = cur.fetchall()
    if not data:
        return 0
    else:
        return data[0][2], data[0][3], data[0][4], data[0][5]
    

def get_video_count():
    conn, cur = get_conn()
    cur.execute("SELECT SUM(video) FROM count")
    data = cur.fetchall()
    if data == 0 or not data:
        return 0
    else:
        return data[0][0]


def check_user(username_id):
    t = (username_id, )
    conn, cur = get_conn()
    cur.execute("SELECT COUNT(*) FROM users WHERE username = ?",t)
    users = cur.fetchall()
    if(users[0][0] == 0):
        return False
    else:
        return True
    
def check_radiation(username_id):
    t = (username_id, )
    conn, cur = get_conn()
    cur.execute("SELECT COUNT(*) FROM radiation WHERE username = ?",t)
    users = cur.fetchall()
    if(users[0][0] == 0):
        return False
    else:
        return True

def add_user(username_id):
    conn, cur = get_conn()
    t = (username_id, 0, )
    cur.execute("INSERT INTO users(username, points) VALUES(?,?)", t)
    conn.commit()


def add_radiation(username_id):
    conn, cur = get_conn()
    t = (username_id, 0, 0, )
    cur.execute("INSERT INTO radiation(username, exposure, hazmat) VALUES(?,?,?)", t)
    conn.commit()



def add_points_user(username_id, points):
    conn, cur = get_conn()
    t = (points, username_id, )
    cur.execute("UPDATE users SET points = points + ? WHERE username = ?", t)
    conn.commit()

def add_exposure_user(username_id, points):
    conn, cur = get_conn()
    t = (points, username_id, )
    cur.execute("UPDATE radiation SET exposure = exposure + ? WHERE username = ?", t)
    conn.commit()

def add_exposure_daily():
    conn, cur = get_conn()  
    cur.execute("UPDATE radiation SET exposure = exposure + 1 WHERE 0 = 0")
    conn.commit()

def add_hazmat_user(username_id, points):
    conn, cur = get_conn()
    t = (points, username_id, )
    cur.execute("UPDATE radiation SET hazmat = ? WHERE username = ?", t)
    conn.commit()

def remove_points(username_id, points):
    conn, cur = get_conn()
    t = (points, username_id, )
    t2 = (username_id, )
    cur.execute("UPDATE users SET points = points - ? WHERE username = ?", t)
    cur.execute("UPDATE users SET points = 0 WHERE username = ? AND points < 0", t2)
    conn.commit()

def remove_exposure(username_id, exposure):
    conn, cur = get_conn()
    t = (exposure, username_id, )
    t2 = (username_id, )
    cur.execute("UPDATE radiation SET exposure = exposure - ? WHERE username = ?", t)
    cur.execute("UPDATE radiation SET exposure = 0 WHERE username = ? AND exposure < 0", t2)
    conn.commit()

def remove_hazmat(username_id, exposure):
    conn, cur = get_conn()
    t = (exposure, username_id, )
    t2 = (username_id, )
    cur.execute("UPDATE radiation SET hazmat = hazmat - ? WHERE username = ?", t)
    cur.execute("UPDATE radiation SET hazmat = 0 WHERE username = ? AND hazmat < 0", t2)
    conn.commit()

def add_points(username, points):
    if(check_user(username) == False and check_character(username)):
        add_user(username)
        add_points_user(username ,points)
    elif(check_character(username)):
        add_points_user(username,points)

def add_exposure(username, points):
    if(check_radiation(username) == False and check_character(username)):
        add_radiation(username)
        add_exposure_user(username ,points)
    elif(check_radiation(username)):
        add_exposure_user(username,points)

def add_hazmat(username, points):
    if(check_radiation(username) == False and check_character(username)):
        add_radiation(username)
        add_hazmat_user(username ,points)
    elif(check_radiation(username)):
        add_hazmat_user(username,points)

def add_leaderboard(username, message_id, count):
    conn, cur = get_conn()
    now=datetime.now()
    timestamp=datetime.timestamp(now)
    t = (username, message_id, timestamp, 1, count, )
    cur.execute("INSERT INTO board_tables(username, message_id, created_time, page_number, last_usernumber) VALUES(?,?,?,?,?)", t)
    conn.commit()

def check_leaderboard(message_id, user_id):
    conn, cur = get_conn()
    t = (user_id, message_id, )
    cur.execute("SELECT COUNT(*) FROM board_tables WHERE username = ? AND message_id = ?",t)
    data = cur.fetchall()
    if(data[0][0] == 0):
        return False
    else:
        return True

def get_user_point(username_id):
    conn, cur = get_conn()
    t = (username_id, )
    cur.execute("SELECT * FROM users WHERE username = ?", t)
    data = cur.fetchall()
    if not data:
        return 0
    else:
        return data[0][2]
    
def get_user_exposure(username_id):
    conn, cur = get_conn()
    t = (username_id, )
    cur.execute("SELECT * FROM radiation WHERE username = ?", t)
    data = cur.fetchall()
    if not data:
        return 0
    else:
        return data[0][2]
    
def get_user_hazmat(username_id):
    conn, cur = get_conn()
    t = (username_id, )
    cur.execute("SELECT * FROM radiation WHERE username = ?", t)
    data = cur.fetchall()
    if not data:
        return 0
    else:
        return data[0][3]


def get_leaderboard_page(message_id):
    conn, cur = get_conn()
    t = (message_id, )
    cur.execute("SELECT * FROM board_tables WHERE AND message_id = ?",t)
    data = cur.fetchall()
    return data[0][4], data[0][5]

def update_leaderboard(page, last_user, message_id):
    conn, cur = get_conn()
    t = (page, last_user, message_id)
    cur.execute("UPDATE board_tables SET page_number = ? , last_usernumber = ? WHERE message_id = ?", t)
    conn.commit()

def get_users():
    conn, cur = get_conn()
    cur.execute("SELECT * FROM users ORDER BY points DESC")
    rows = cur.fetchall()
    return rows

def get_radiation():
    conn, cur = get_conn()
    cur.execute("SELECT * FROM radiation ORDER BY exposure DESC")
    rows = cur.fetchall()
    return rows

def get_hazmat():
    conn, cur = get_conn()
    cur.execute("SELECT * FROM radiation ORDER BY hazmat DESC")
    rows = cur.fetchall()
    return rows

def get_rank_users(username):
    conn, cur = get_conn()
    t = (username, )
    cur.execute("""
    SELECT 
            t2.rank
    FROM users t1
    INNER JOIN
    (
        SELECT t1.points,
        (SELECT COUNT(*) FROM (SELECT DISTINCT points FROM users) t2
        WHERE t2.points >= t1.points) rank
        FROM (SELECT DISTINCT points FROM users) t1
    ) t2
        ON t1.points = t2.points
        WHERE username = ?
    """, t)
    rows = cur.fetchall()
    return rows

#가입한 순서로도 하나 더 걸어주면 좋고, 정렬 조건을 하나 더. 30분마다 갱신. 새로운 값을 넣는 테이블에 58분꺼, 전에는 48분에 업데이트됏을텐데... 
# 뉴를 올드로 옮기고 새로운 상태를 뉴에 넣고. 
# 칼럼을 추가하는데, users에, 이모지랑 네임을 추가를 하고, 오너라는 항목에 디스코드 아이디, 검색할때 
# 업데이트 이모지... 이모지 없을때 
# 2025-08: ^ 얘 뭐래는거임?? 

async def delete_character(character):
    conn, cur = get_conn()
    t = (character, )
    cur.execute("DELETE FROM users WHERE username = ?", t)
    conn.commit()

async def reset_database():
    conn, cur = get_conn()
    cur.execute("DELETE FROM users WHERE 'a' = 'a'")
    conn.commit()

async def reset_count():
    conn, cur = get_conn()
    cur.execute("DELETE FROM count WHERE 0 = 0")
    conn.commit()

async def reset_radiation():
    conn, cur = get_conn()
    cur.execute("DELETE FROM radiation WHERE 0 = 0")
    conn.commit()

async def reset_radiation_player(username):
    conn, cur = get_conn()
    t = (username, )
    cur.execute("UPDATE radiation SET exposure = 0 WHERE username = ?", t)
    conn.commit()
