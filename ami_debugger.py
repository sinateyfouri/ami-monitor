import asterisk.manager 
import sys 
import os
import time


def handle_shutdown(event, manager):
   print("Recieved shutdown event")
   manager.close()
   # we could analize the event and reconnect here

def handle_event(event, manager):
   # print(event)
   print("Recieved event: %s" % event.headers)

   # #Sina Teyfouri
   # if event.name == 'NewCallerid':
   #    newcaller = event.headers
   #    callerid = newcaller.get('CallerIDNum')
   #    print(f'Caller id is : {callerid}')
   # if event.name == 'DeviceStateChange' :
   #    stat = event.headers
   #    extensionstatus = stat.get('State')
   #    if extensionstatus == 'RINGING' :
   #       extension = stat.get('Device')
   #       print(f'Calling to {extension}')
   # if event.name == 'Hangup' :
   #    stat = event.headers
   #    extensionstatus = stat.get('Uniqueid')
   #    print(f'Uniqe id {extensionstatus} just hanged up')

manager = asterisk.manager.Manager()
try:
    # connect to the manager
    try:
       
       manager.connect('127.0.0.1')
       manager.login('Sina', 'Sina@79344241!')

        # register some callbacks
       manager.register_event('Shutdown', handle_shutdown) # shutdown
       manager.register_event('*', handle_event)           # catch all
      #  manager.event_dispatch()

        # get a status report
       response = manager.status()

      #  manager.logoff()
    except asterisk.manager.ManagerSocketException as e:
      #  print("Error connecting to the manager: %s" % e.strerror)
       sys.exit(1)
    except asterisk.manager.ManagerAuthException as e:
       print("Error logging in to the manager: %s" % e.strerror)
       sys.exit(1)
    except asterisk.manager.ManagerException as e:
       print("Error: %s" % e.strerror)
       sys.exit(1)

except:
   # remember to clean up
   manager.close()

try:
    while True:
        time.sleep(10)
except (KeyboardInterrupt, SystemExit):
    manager.close()