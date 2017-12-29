import time
import traceback as tb
import pickle
import requests
import sys
import os.path
from collections import defaultdict, deque
from datetime import datetime
from config import *

### Message Queues ###
last_message = datetime(2000, 1, 1)
priority_queue = []
message_queue = []

def group_value_factory():
    return deque(maxlen = 100)

### Price Tracking ###
type_groups = None
group_price = defaultdict(group_value_factory)

### Write price data ###
last_save = datetime(2000, 1, 1)

def main():
    s = requests.Session();
    s.headers.update({'User-Agent': user_agent, 'Accept': 'text/json'})

    # load our type mapping
    with open('ship_ids', 'r') as input:
        type_groups = pickle.load(input)

    # load our price history
    if os.path.isfile('group_avg'):
        with open('group_avg', 'r') as input:
            group_price = pickle.load(input)

    while True:
        # fetch kills from zkillboard
        try:
            kill = fetch_zkill(s)
            if kill:

                # 2017-09-30T23:40:34Z
                kill_date = datetime.strptime(kill['killmail']['killmail_time'], '%Y-%m-%dT%H:%M:%SZ')
                if (datetime.utcnow() - kill_date).total_seconds() >= 86400:
                    # Old kill, probably a recalc.  Skip!
                    continue

                # print kill
                print_kill(kill)

                # check to see if we want to add kill to the queues
                if check_priority(kill):
                    priority_queue.append(kill['killID'])
                elif check_intersting(kill):
                    message_queue.append(kill['killID'])

            # check if there is anything to post
            process_queues();

            # check if we need to save price data
            save();
        except:
            sys.stderr.write(tb.format_exc() + '\n')
            if locals().get('kill'):
                sys.stderr.write('Kill Information')
                sys.stderr.write(str(kill) + '\n')

def save():
    global last_save

    if (datetime.now() - last_save).total_seconds() > 60:
        with open('group_avg', 'w') as output:
            pickle.dump(group_price, output)

        # update timestamp
        last_save = datetime.now()

def check_average(value, group_id):
    global zkill_value_modifier, zkill_value_minimum

    group_values = group_price[group_id]
    valuable = False
    if len(group_values) > 20 and group_id != 0 and zkill_value_modifier:
        valuable = value >= (float(sum(group_values)) / len(group_values) * zkill_value_modifier)

    # add this price to our average ticker
    if zkill_value_modifier and value >= zkill_value_minimum:
        group_values.append(value)

    return valuable

def check_priority(kill):
    # if this is a watched kill or loss add it to the priority queue
    if 'corporation_id' in kill['killmail']['victim'] and kill['killmail']['victim']['corporation_id'] in priority_corps:
        return True
    elif 'character_id' in kill['killmail']['victim'] and kill['killmail']['victim']['character_id'] in priority_chars:
        return True
    else:
        for attacker in kill['killmail']['attackers']:
            if 'corporation_id' in attacker and attacker['corporation_id'] in priority_corps:
                return True
            if 'character_id' in attacker and attacker['character_id'] in priority_chars:
                return True
    
    return False

def check_intersting(kill):
    # check the price of this kill against the average value
    if check_average(kill['zkb']['totalValue'], type_groups[kill['killmail']['victim']['ship_type_id']]):
        return True
    
    # if this is a fancy kill add it to the message queue
    elif zkill_value_threshold and kill['zkb']['totalValue'] > zkill_value_threshold:
        return True
    
    return False

def process_queues():
    global last_message, priority_queue, message_queue

    # check for priority queue first
    if len(priority_queue) and (datetime.now() - last_message).total_seconds() > priority_interval:
        process_queue(priority_queue)
        priority_queue = []
    # then check our standard queue
    elif len(message_queue) and (datetime.now() - last_message).total_seconds() > message_interval:
        process_queue([message_queue.pop()])

    # queue cleanup
    if len(message_queue) > 10:
        message_queue = message_queue[:10]

def process_queue(queue):
    global last_message
    last_message = datetime.now()
    if len(queue) > bulk_post_threshold:
        # build our text string
        text = '\n'.join([zkillboard_url.format(id = killID) for killID in queue])
        # post the message to GroupMe
        post_message(text)
    else:
        for killID in queue:
            post_message(zkillboard_url.format(id = killID))

def post_message(text):
    if bot_id:
        payload = {
            'bot_id': bot_id,
            'text': text
        }
        requests.post(groupme_url, data=payload)

def fetch_zkill(session):
    r = session.get(redisq_url)

    # pull json data from the response
    try:
        data = r.json()
    except ValueError:
        return None

    if 'package' in data and data['package'] is not None:
        return data['package']
    return None

def print_kill(kill):

    print "{date} > {killID} | {value}".format(
        date=datetime.now(), 
        killID=kill['killID'], 
        value=format_isk(kill['zkb'].get('totalValue', 0.0))
    )

def format_isk(num):
    BILLION = 1000000000
    MILLION = 1000000
    THOUSAND = 1000

    if num > BILLION:
        return "{:,.0f} B".format(num / BILLION)
    elif num > MILLION:
        return "{:,.0f} M".format(num / MILLION)
    else:
        return "{:,.0f} K".format(num / THOUSAND);

if __name__ == "__main__":
    main()
