#!/usr/bin/env python3.12
import configparser
import logging
import os
import time
import sys
import requests
import asterisk.manager 

# Setup logging
log_dir = "/var/log/ami_monitor"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "ami_monitor.log"),
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

# Load config
config = configparser.ConfigParser()
config.read('/etc/ami_monitor/config.ini')

host = config.get('asterisk', 'host')
port = config.getint('asterisk', 'port')
username = config.get('asterisk', 'username')
secret = config.get('asterisk', 'secret')
api_url = config.get('api', 'url')


# active_calls = {}

def send_call_info(caller, dest):
    try:
        params = {
            "callNumber": caller,
            "destNumber": dest
        }
        response = requests.get(api_url, params=params, timeout=5)
        if response.status_code in (200, 204):
            logging.info(f"[API] Sent: {caller} -> {dest}")
        else:
            logging.warning(f"[API] Response {response.status_code}: {response.text}")
    except Exception as e:
        logging.error(f"[API] Exception: {str(e)}")



def handle_shutdown(event, manager):
   print("Recieved shutdown event")
   manager.close()

call_sessions = {}
def handle_event(event, manager):

    name = event.name
    h = event.headers
    uniqueid = h.get('Uniqueid')
    linkedid = h.get('Linkedid') 
    callerid = h.get('CallerIDNum')
    if name == 'Newchannel' and uniqueid == linkedid:
        call_sessions[linkedid] = {
            'caller': callerid,
            'extension': None,
            'created': time.time()
        }
        logging.info(f"[NewCall] Caller {callerid}, Linkedid: {linkedid}")
    elif name == 'Newchannel' and uniqueid != linkedid:
        session = call_sessions.get(linkedid)
        if session and callerid and callerid.isdigit():
            session['extension'] = callerid
            logging.info(f"[Match] Call {linkedid} matched with extension {callerid}")
            send_call_info(session['caller'], callerid)
            call_sessions.pop(linkedid, None)

    elif name == 'Hangup':
        if linkedid in call_sessions:
            logging.info(f"[Hangup] Incomplete call ended: {linkedid}")
            call_sessions.pop(linkedid, None)
        
    # category = ('NewCallerid', 'DeviceStateChange', 'Hangup', 'RINGING' )
    # if event.name in category:        
    #     if event.name == 'NewCallerid':        
    #         newcaller = event.headers
    #         callerid = newcaller.get('CallerIDNum')
    #         logging.info(f'Caller id is : {callerid}')
    #         active_calls['callerid'] = callerid 
    #     if event.name == 'DeviceStateChange' :
    #         stat = event.headers
    #         extensionstatus = stat.get('State')
    #         if extensionstatus == 'RINGING' :
    #             extension = stat.get('Device')
    #             logging.info(f'Calling to {extension}')
    #             active_calls['extension'] = extension
    #             logging.info(active_calls) 
    #             callernumber = active_calls.get('callerid')   
    #             exten = active_calls.get('extension')
    #             send_call_info(callernumber, exten )
    #     if event.name == 'Hangup' :
    #         stat = event.headers
    #         extensionstatus = stat.get('Uniqueid')
    #         logging.info(f'Uniqe id {extensionstatus} just hanged up')



manager = asterisk.manager.Manager()
try:
    manager.connect(host)
    manager.login(username, secret)
    manager.register_event('Shutdown', handle_shutdown) # shutdown
    manager.register_event('*', handle_event)           # catch all
    response = manager.status()

except (KeyboardInterrupt, SystemExit):
    manager.close()
try:
    while True:
        time.sleep(10)
except (KeyboardInterrupt, SystemExit):
    manager.close()