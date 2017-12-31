user_agent = 'QS - zKill Monitor'

### Watchlists ###
priority_corps = []
priority_chars = []
excluded_ids = []

zkill_value_threshold = 40000000000
zkill_value_modifier = 2.5
zkill_value_minimum = 500000000
zkill_priority_value_minimum = 15000000

### Message Intervals (Seconds) ###
priority_interval = 60*1
message_interval = 60*45

### Message Settings ###
bulk_post_threshold = 5

### GroupMe Configurations ###
bot_id = ''
priority_bot_id = ''
groupme_url = 'https://api.groupme.com/v3/bots/post'

### Zkillboard Configurations ###
zkillboard_url = "https://zkillboard.com/kill/{id}/"
redisq_url = 'https://redisq.zkillboard.com/listen.php'