import pandas as pd
import sqlite3
from pprint import pprint

pd.set_option('max_columns',15)
pd.set_option('display.width', 10000)
db_file = "Binance.db"
connection = sqlite3.connect(db_file)
cursor = connection.cursor()

def create_db(con=connection, cur=cursor):
    cur.execute("""CREATE TABLE trade_history (
                    symbol text,
                    id integer,
                    orderId integer,
                    side text,
                    price real,
                    qty real,
                    realizedPnl real,
                    marginAsset text,
                    quoteQty real,
                    commission real,
                    commissionAsset text,
                    time integer,
                    positionSide text,
                    buyer text,
                    maker text
    )""")
    con.commit()
    con.close()

def query(con, cur):
    result = pd.read_sql_query("SELECT * FROM trade_history", con)
    print(result)
    print('Total PNL: ',result['realizedPnl'].sum())
    con.close()

def delete(con, cur):
    cur.execute("DELETE FROM trade_history")
    con.commit()
    con.close()

if __name__ == '__main__':
    #delete(connection, cursor)
    query(connection, cursor)
    #create_db()
