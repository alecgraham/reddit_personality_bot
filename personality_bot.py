import praw
import time
import datetime
from config import *
from reddit_profile import reddit_profile

def getUserName(message):
    my_user = '/u/' + reddit_username
    mention_index = message.find(my_user)
    if mention_index < 0:
        return None
    user_start = mention_index + len(my_user) + 1
    end_chars = [message.find(' ',user_start),message.find('\n',user_start)]
    user_end = min(end_chars[0] if end_chars[0] > 0 else end_chars[1],end_chars[1] if end_chars[1] > 0 else end_chars[0])
    if user_end < 0:
        user_end = None
    return message[user_start:user_end].replace('\\','') # b/c robot_hank_scorpio likes playing games

def main():
    reddit = praw.Reddit(client_id=reddit_id,
                         client_secret=reddit_secret,
                         password=reddit_password,
                         user_agent=reddit_agent,
                         username=reddit_username)

    #for mention in reddit.inbox.mentions(limit=25):
        #print('{}\n{}\n'.format(mention.author, mention.body))
    last_comment = None
    while True:
        unread_messages =[]
        for item in reddit.inbox.unread(limit=None):
            username = getUserName(item.body)
            if username:
                profile = reddit_profile(username)
                now = datetime.datetime.now()
                timedelta = now - (last_comment or now)
                #avoid reddit comment 10 min ratelimit for now
                if 0 < timedelta.seconds < 10*60:
                    time.sleep(10*60 - timedelta.seconds)
                while True:
                    try:
                        item.reply(profile.description)
                        last_comment = datetime.datetime.now()
                        break
                    except:
                        time.sleep(60)
            unread_messages.append(item)
        reddit.inbox.mark_read(unread_messages)
        time.sleep(60)


main()
