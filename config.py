WDTtimval=2000
WDTcon=0 # Cyciling counter for WDT
WDTtrigger=15 # Threshold for machine resets
WDTobj=0 # Container variable for timer object
WDT_enable=1 # Set to 1 to enable WDT
AP_IP = ('192.168.1.12', '255.255.255.0', '192.168.1.1', '8.8.8.8')
ESSID='fbadmin'
PASS_ESSID='admin12345'

# to dynamically change the WDT time-to-reset parameter in main loop
#WDTkill()
#c.WDTtrigger=<new value>
#WDTfeed() # To restart the WDT