from glob import iglob
from typing import Optional, List, Sequence
from sqlparse.tokens import Keyword, DDL, Token, Name, Punctuation
from sqlparse.sql import Statement
import sqlparse
import os

TokenType = Token.__class__
DEFAULT_DB = "default"

def find_hive_ddl(ddl_folder_path: str, table_name: str, db_name: Optional[str]=None):
    """引数で指定したテーブルの定義スクリプトをフォルダから探し出す関数"""
    for p in iglob(ddl_folder_path, recursive=True):
        if not os.path.isfile(p):
            continue
        with open(p) as f:
            if find_table_definition(f, table_name, db_name):
                return p
    raise FileNotFoundError(
        "DDL file of {table_name} not found.".format(table_name=table_name)
    )

def find_table_definition(sql: str, table_name: str, db_name: Optional[str]=None) -> Optional[TokenType]:
    """`table_name`で指定したテーブルの定義を文字列`sql`中から見つける"""
    db_name = db_name or DEFAULT_DB
    # 1. パースしてトークン列に分割
    for query in sqlparse.parse(sql):
        tokens = [t for t in query.flatten() if not (t.is_whitespace or is_comment(t))]
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
        if db_name == DEFAULT_DB and match_consume(tokens, (Name, table_name)):
            return query
        if (match_consume(tokens, (Name, db_name))
                and match_consume(tokens, (Punctuation, "."))
                and match_consume(tokens, (Name, table_name))
            ):
            return query

def is_comment(token: TokenType) -> bool:
    return token.ttype in sqlparse.tokens.Comment

def match_consume(tokens: List[TokenType], match_args: Sequence) -> bool:
    if tokens[0].match(*match_args):
        tokens.pop(0)
        return True
    return False
