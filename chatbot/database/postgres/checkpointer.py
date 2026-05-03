from langgraph.checkpoint.postgres import PostgresSaver
from database.postgres.db import pool

def get_checkpointer():
    # ✅ Use 'conn' if your LangGraph version deprecated 'pool'
    with pool.connection() as conn:
        cp = PostgresSaver(conn)
        cp.setup()
        return cp