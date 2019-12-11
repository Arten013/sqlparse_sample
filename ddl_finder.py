from glob import iglob
from typing import Optional, List, Iterable
from sqlparse.tokens import Keyword, DDL, Token, Name, Punctuation
import sqlparse
from pathlib import Path

TokenType = Token.__class__
DEFAULT_DB = "default"


def find_hive_ddl(directory: str, table: str, db: Optional[str] = None):
    """引数で指定したテーブルの定義スクリプトをフォルダから探し出す関数"""
    for p in iglob(directory, recursive=True):
        path = Path(p)
        if not path.is_file():
            continue
        with p.open() as f:
            if find_table_definition(f.read(), table, db):
                return p
    raise FileNotFoundError(
        "DDL file of {table_name} not found.".format(table_name=table)
    )


def find_table_definition(
        sql: str, table: str, db: Optional[str] = None) -> Optional[TokenType]:
    """`table_name`で指定したテーブルの定義を文字列`sql`中から見つける"""
    db = db or DEFAULT_DB
    # 1. パースしてトークン列に分割
    for query in sqlparse.parse(sql):
        tokens = [
            t for t in query.flatten()
            if not (t.is_whitespace or is_comment(t))
        ]
        # 2. <DDL CREATE>を検証
        if not match_consume(tokens, (DDL, "CREATE")):
            continue
        # 3. <Keyword TEMPORARY> <Keyword EXTERNAL> をスキップ
        match_consume(tokens, (Keyword, "TEMPORARY"))
        match_consume(tokens, (Keyword, "EXTERNAL"))
        # 4. <Keyword TABLE>を検証
        if not match_consume(tokens, (Keyword, "TABLE")):
            continue
        # 5. <Keyword IF>, <Keyword NOT>, <Keyword EXISTS>をスキップ
        if match_consume(tokens, (Keyword, "IF")):
            if not match_consume(tokens, (Keyword, "NOT")):
                continue
            if not match_consume(tokens, (Keyword, "EXISTS")):
                continue
        # 6. テーブル名が一致したら返す。
        if db == DEFAULT_DB and match_consume(tokens, (Name, table)):
            return query
        if (match_consume(tokens, (Name, db))
                and match_consume(tokens, (Punctuation, "."))
                and match_consume(tokens, (Name, table))
        ):
            return query


def is_comment(token: TokenType) -> bool:
    return token.ttype in sqlparse.tokens.Comment


def match_consume(tokens: List[TokenType], match_args: Iterable) -> bool:
    if tokens[0].match(*match_args):
        tokens.pop(0)
        return True
    return False
