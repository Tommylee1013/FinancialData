from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ChatStore:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("pragma journal_mode=wal")
        connection.execute("pragma foreign_keys=on")
        return connection

    def _initialize(self):
        with self.connect() as con:
            con.executescript("""
              create table if not exists conversations (
                id text primary key, title text not null, created_at text not null,
                updated_at text not null, context_json text not null default '{}'
              );
              create table if not exists messages (
                id integer primary key autoincrement, conversation_id text not null,
                role text not null check(role in ('user','assistant','system')),
                content text not null, created_at text not null, response_id text,
                input_tokens integer, output_tokens integer,
                foreign key(conversation_id) references conversations(id) on delete cascade
              );
              create table if not exists tool_calls (
                id integer primary key autoincrement, conversation_id text not null,
                message_id integer, tool_name text not null, arguments_json text not null,
                result_json text not null, created_at text not null,
                foreign key(conversation_id) references conversations(id) on delete cascade
              );
            """)

    def create_conversation(self, title="New research", context=None):
        conversation_id = uuid.uuid4().hex
        now = utc_now()
        with self.connect() as con:
            con.execute("insert into conversations values (?,?,?,?,?)",
                        [conversation_id, title, now, now, json.dumps(context or {})])
        return self.get_conversation(conversation_id, include_messages=True)

    def list_conversations(self):
        with self.connect() as con:
            rows = con.execute("""
              select c.*, count(m.id) message_count from conversations c
              left join messages m on m.conversation_id=c.id
              group by c.id order by c.updated_at desc
            """).fetchall()
        return [dict(row) | {"context": json.loads(row["context_json"])} for row in rows]

    def get_conversation(self, conversation_id, include_messages=False):
        with self.connect() as con:
            row = con.execute("select * from conversations where id=?", [conversation_id]).fetchone()
            if not row:
                return None
            result = dict(row) | {"context": json.loads(row["context_json"])}
            if include_messages:
                result["messages"] = [dict(item) for item in con.execute(
                    "select * from messages where conversation_id=? order by id", [conversation_id]).fetchall()]
        return result

    def add_message(self, conversation_id, role, content, **metadata):
        now = utc_now()
        with self.connect() as con:
            cursor = con.execute("""
              insert into messages(conversation_id,role,content,created_at,response_id,input_tokens,output_tokens)
              values(?,?,?,?,?,?,?)
            """, [conversation_id, role, content, now, metadata.get("response_id"),
                  metadata.get("input_tokens"), metadata.get("output_tokens")])
            con.execute("update conversations set updated_at=? where id=?", [now, conversation_id])
            return cursor.lastrowid

    def rename_from_first_message(self, conversation_id, content):
        title = " ".join(content.strip().split())[:64] or "New research"
        with self.connect() as con:
            count = con.execute("select count(*) from messages where conversation_id=?", [conversation_id]).fetchone()[0]
            if count <= 1:
                con.execute("update conversations set title=? where id=?", [title, conversation_id])

    def add_tool_call(self, conversation_id, message_id, name, arguments, result):
        with self.connect() as con:
            con.execute("""insert into tool_calls(conversation_id,message_id,tool_name,arguments_json,result_json,created_at)
                           values(?,?,?,?,?,?)""",
                        [conversation_id, message_id, name, json.dumps(arguments), json.dumps(result, default=str), utc_now()])

    def delete_conversation(self, conversation_id):
        with self.connect() as con:
            return con.execute("delete from conversations where id=?", [conversation_id]).rowcount > 0
