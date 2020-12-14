import requests
import re
import pprint
import urllib3
import logging
import sched
import time
import datetime
import argparse

urllib3.disable_warnings()
requests.adapters.DEFAULT_RETRIES = 2
logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s',
    handlers = [logging.StreamHandler()])

def update_monitors(uptime_dict, api_key):
    try:
        get_monitors_resp = requests.post('https://api.uptimerobot.com/v2/getMonitors', data={
            'api_key': api_key,
            'format': 'json'
        })
        get_monitors_data = get_monitors_resp.json()
        monitors = get_monitors_data['monitors']
        
        for monitor in monitors:
            if monitor['url'] in uptime_dict.keys():
                uptime_dict[monitor['url']][3] = monitor['id']
            
            # Lerm's site uses a different ping in uptimerobot that doesn't include the protocol. Handle that here
            elif monitor['url'] == 'crewlink.glitch.me':
                uptime_dict['https://crewlink.glitch.me'][3] = monitor['id']

        for k, v in uptime_dict.items():
            edit_monitor_req = requests.post('https://api.uptimerobot.com/v2/editMonitor', data={
                'api_key': api_key,
                'id': v[3],
                'friendly_name': f"{v[0]} | {k} | {v[1]} | {v[2]} ({datetime.datetime.utcnow().strftime('%H:%M:%S UTC')})" 
            }) 
            logging.info(f"{k}: {edit_monitor_req.status_code}")
    except Exception as e:
        logging.error(e)
    

def main(s, api_key):
    uptime_dict = {
        'https://crewlink.among-us.tech': [
            'Cobchise',
            'NA',
            '',
            ''
        ],
        'https://crewlink.glitch.me': [
            'Lermatroid',
            'NA',
            '',
            ''
        ],
        'https://crewl.ink': [
            'Ottomated',
            'NA',
            '',
            ''
        ],
        'https://s1.theskeld.xyz': [
            'The Skeld #1',
            'OCE',
            '',
            ''
        ],
        'https://s2.theskeld.xyz': [
            'The Skeld #2',
            'NA',
            '',
            ''
        ],
        'https://s3.theskeld.xyz': [
            'The Skeld #3',
            'NA',
            '',
            ''
        ],
        'https://s4.theskeld.xyz': [
            'The Skeld #4',
            'EU',
            '',
            ''
        ],
        'https://public2.crewl.ink': [
            'ubergeek77',
            'NA',
            '',
            ''
        ]
    }

    # Default
    pattern = re.compile(r"There are currently (?P<count>\w+) connected users.")

    # TheSkeld
    pattern2 = re.compile(r"There are currently (?P<count>\w+) users connected to this Crew Link Server.")
    
    logging.info("Updating uptimerobot")
    count_dict = {}
    for server in uptime_dict.keys():
        try: 
            resp = requests.get(server, verify=False, timeout=3)
            count = re.search(pattern, resp.content.decode())
            if not count:
                count = re.search(pattern2, resp.content.decode())
                if not count:
                    raise Exception(f"{server}: Regex could not find connected user count and scraping failed. Is the site using a custom index page?")

            count_dict[server] = count.group('count') 
            if server in uptime_dict.keys():
                uptime_dict[server][2] = f"{count.group('count')} users"
        except Exception as e:
            logging.error(e)
            uptime_dict[server][2] = "Down"

    logging.info("Updating monitors")
    update_monitors(uptime_dict, api_key)

    logging.info("Scheduling job in 20 minutes")
    s.enter(1200, 1, main, (s, api_key))
    logging.info("Waiting 20 minutes")


if __name__=="__main__":
    parser = argparse.ArgumentParser(description="CrewLink UptimeRobot monitor to monitor the status of public CrewLink servers")
    parser.add_argument('api_key', type=str, help='UptimeRobot API Key')
    args = parser.parse_args()

    s = sched.scheduler(time.time, time.sleep)
    logging.info("Established scheduler")
    s.enter(0, 1, main, (s, args.api_key))
    logging.info("Starting jobs")
    s.run()
