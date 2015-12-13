import time
import requests
from datetime import datetime
from config import *

### Message Queues ###
last_message = datetime(2000, 1, 1)
priority_queue = []
message_queue = []

def main():
    s = requests.Session();
    s.headers.update({'User-Agent': user_agent, 'Accept': 'text/json'})
    while True:
        # fetch kills from zkillboard
        kill = fetch_zkill(s)
        if kill:
            # print kill
            print_kill(kill)
            # if this is a watched kill or loss add it to the priority queue
            if kill['killmail']['victim']['corporation']['name'].lower() in priority_corps:
                priority_queue.append(kill['killID'])
            else:
                for attacker in kill['killmail']['attackers']:
                    if 'corporation' in attacker and attacker['corporation']['name'].lower() in priority_corps:
                        priority_queue.append(kill['killID'])
                        break;

            # if this is a fancy kill add it to the message queue
            if kill['zkb']['totalValue'] > zkill_value_threshold:
                message_queue.append(kill['killID'])

        # check if there is anything to post
        process_queues();

def process_queues():
    global last_message, priority_queue, message_queue

    # check for priority queue first
    if len(priority_queue) and (datetime.now() - last_message).total_seconds() > priority_interval:
        process_queue(priority_queue)
        priority_queue = []
    # then check our standard queue
    elif len(message_queue) and (datetime.now() - last_message).total_seconds() > priority_interval:
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
    payload = {
        'bot_id': bot_id,
        'text': text
    }
    requests.post(groupme_url, data=payload)

def fetch_zkill(session):
    r = session.get(redisq_url)
    data = r.json()
    if 'package' in data and data['package'] is not None:
        return data['package']
    return None

def print_kill(kill):
    values = {
        'killID': kill['killID'],
        'shipType': kill['killmail']['victim']['shipType']['name'],
        'value': format_isk(kill['zkb']['totalValue'])
    }

    pilot = list();
    if 'character' in kill['killmail']['victim']: pilot.append(kill['killmail']['victim']['character']['name']) 
    if 'corporation' in kill['killmail']['victim']: pilot.append(kill['killmail']['victim']['corporation']['name']) 
    if 'alliance' in kill['killmail']['victim']: pilot.append(kill['killmail']['victim']['alliance']['name']) 

    print "{date} > {killID} | {value} | {shipType} | {pilot}".format(date = datetime.now(), pilot = ' - '.join(pilot).encode('utf-8'), **values)

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
