import pandas as pd

from psycopg2 import sql

def check_for_keyword(target_words, corpus): #used for checking bio's
    for i in range(len(target_words)):
        if target_words[i] in corpus:
            #print('true')
            return True
        else:
            continue
            
#Target words present in Bio's
target_words = ['not a financial advisor','NOT A FINANCIAL ADVISOR', "DD", 'not financial advice',
                'not recommendations','opinions','views are my own','investing','trader',
                'financial advisor','investor','trading','personal opinion','due diligence',
                'investment advice','not recommendations','tweets are my opinion']

def get_mentions(df):
    mentions = {}
    for tweet_text in df['text']:
        first_strip = tweet_text.strip('b')
        split = first_strip.split()
        #Go through each word in each tweet:
        for word in split:

            if word[0] == '$' and word[1:].isalpha():
                #print(word)
                if word in mentions.keys():
                    mentions[word] = mentions[word] + 1
                elif word.upper() in mentions.keys():
                    mentions[word.upper()] = mentions[word.upper()] + 1
                else:
                    mentions[word] = 1
    return mentions


#With the master dictionary in place and a connection to DB established, this function will handle the upsertion of master_dic to db
def upsert_database(master_dic, cur):
    for symbol in master_dic.keys():
        
        if len(symbol) > 15:
            continue
        
        
        
        ##Execute a query to determine if symbol exists in tickers table:
        cur.execute(sql.SQL('SELECT EXISTS(SELECT 1 FROM tickers WHERE ticker_name=%s) AS "exists";'), (symbol[1:],))
        res = cur.fetchall()[0][0]

        if res == False:
            #print('ticker does not exist in table')
            #ticker does not exist in table, add it
            cur.execute(sql.SQL('INSERT INTO tickers(ticker_name) VALUES (%s) ;'), (symbol[1:],))

        cur.execute(sql.SQL('SELECT ticker_id FROM tickers WHERE ticker_name = %s'), (symbol[1:],))
        ticker_id = cur.fetchall()[0][0]


        for date in master_dic[symbol].keys():
        #now we need to do a insert on conflict update I think
        #Maybe not.
        #determine if there exists an entry in date_mentions where DATE = date AND Ticker ID = TICKER ID
        #if true, update entry
        #if false, create entry.
            # print('\n')
            # print('Date :' + str(date))
            # print('Ticker ID :' + str(ticker_id))
            # print('mentions :' + str(master_dic[symbol][date][0]))
            # print('users :' + 'Not sure about this one')
            # print('outreach_est :' + str(master_dic[symbol][date][1]))

            ##Execute a query to determine if symbol exists in tickers table:
            cur.execute(sql.SQL('SELECT EXISTS(SELECT 1 FROM date_mentions WHERE ticker_id=%s AND date=%s) AS "exists";'), (ticker_id,date,))
            res = cur.fetchall()[0][0]

            if res == False:
                cur.execute(
                sql.SQL("INSERT INTO date_mentions (date, ticker_id, mentions, users, estimated_outreach) VALUES (%s, %s, %s, %s, %s)"), #SQL
                (date, ticker_id, master_dic[symbol][date][0], 1, (master_dic[symbol][date][1])) #Values passed in
                )
            else:
                cur.execute(
                sql.SQL("""
                UPDATE date_mentions
                SET
                mentions = mentions + %s,
                users = users + 1,
                estimated_outreach = estimated_outreach + %s
                WHERE date = %s AND ticker_id = %s
                """), #SQL
                (master_dic[symbol][date][0], master_dic[symbol][date][1], date, ticker_id) #Values passed in
                )

    return

def update_users_table(users_df, cur):


    return

def get_follower_count(user_id, cur):

    query = "SELECT follower_count FROM users WHERE twitter_id = %s"
    cur.execute(query, (user_id,))
    follower_count = cur.fetchall()

    return follower_count

def gen_master_dic(df):
    master_dic = {}
    for entry in df.iterrows():
        striped = entry[1][1].strip('b').strip('""')
        if striped[0] and striped[-1] == "'":
            striped = striped.strip("'")
        split = striped.split()

        for word in split:

            word = word.upper()
            if word[0] == '$' and word[1:].isalpha():
                # print(word)
                #Check if ticker symbol is present in master dic
                if word in master_dic.keys():
                    #Check if date is present in ticker dic
                    if entry[0] in master_dic[word].keys():
                        #if it is present, add one to its value
                        master_dic[word][entry[0]] += 1
                    else:
                        #if it is not present, add it with a value of 1
                        master_dic[word][entry[0]] = 1    
                #If ticker is not present, add it
                else:
                    master_dic[word] = {}
                    master_dic[word][entry[0]] = 1
    return master_dic

def get_df(path_to_csv):
    df = pd.read_csv(path_to_csv)
    #Clean df so created_at only shows date:
    for i in df.index:
        df.at[i, 'created_at'] = df.at[i, 'created_at'][0:-9]
    #data frame indexed by date created?
    df = df.set_index("created_at")
    return df

# def get_ticker(config, ticker):
#     conn = psycopg2.connect(
#         host=config.host,
#         database=config.database,
#         user=config.user,
#         password=config.password)
#     cur = conn.cursor()
#     conn.autocommit = True
    
#     query = 'SELECT * FROM ' + ticker +';'
#     cur.execute(query)
#     res = cur.fetchall()
    
#     cur.close()
#     conn.close()
#     return res

