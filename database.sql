PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "users" (
        "ID"    INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        "username"      TEXT,
        "points"        INTEGER
);

CREATE TABLE IF NOT EXISTS "radiation" (
        "ID"    INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        "username"      TEXT,
        "exposure"      INTEGER,
        "hazmat"        INTEGER
);


CREATE TABLE IF NOT EXISTS "board_tables" (
        "ID"    INTEGER PRIMARY KEY AUTOINCREMENT,
        "username"      TEXT,
        "message_id"    TEXT,
        "created_time"  INTEGER,
        "page_number"   INTEGER,
        "last_usernumber"       INTEGER
);

CREATE TABLE IF NOT EXISTS "count" (
        "ID"    INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        "username"      TEXT,
        "clean"        INTEGER,
        "search"        INTEGER,
        "gamble"        INTEGER,
        "video"         INTEGER
);


-- character metadata migrated from owners.json, characters.json, emoji.json
CREATE TABLE IF NOT EXISTS "characters_meta" (
        "char_id"      TEXT PRIMARY KEY,
        "name"         TEXT,
        "emoji"        TEXT,
        "owner_id"     TEXT
);

-- radiation description texts migrated from items/*.txt
CREATE TABLE IF NOT EXISTS "radiation_texts" (
        "ID"    INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        "bucket"        TEXT, -- one of: ten, twentyfive, fifty, seventyfive, hundred, secret
        "text"          TEXT
);


DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('users',6);
INSERT INTO sqlite_sequence VALUES('count',8);
INSERT INTO sqlite_sequence VALUES('board_tables',9);
INSERT INTO sqlite_sequence VALUES('radiation',6);
COMMIT;
