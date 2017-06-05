import sys
import getopt
import json

from eventdata.parameter_sources.randomevent import RandomEvent

raw_mode = False
documents_to_generate = 1000000

try:
    options, remainder = getopt.getopt(
        sys.argv[1:],
        'c:r',
        ['count=',
         'raw',
         ])
except getopt.GetoptError as err:
    print('ERROR:', err)
    sys.exit(1)

for opt, arg in options:
    if opt in ('-c', '--count'):
        if arg.isdigit():
            documents_to_generate = int(arg)
            if documents_to_generate < 1:
                print("ERROR: -c/--count must be followed by a positive integer.")
                sys.exit(0)
        else:
            print("ERROR: -c/--count must be followed by a positive integer.")
            sys.exit(0)
    elif opt in ('-r', '--raw'):
        raw_mode = True

randomevent = RandomEvent({})

for k in range(documents_to_generate):
    evt, idx, typ = randomevent.generate_event()
    
    if raw_mode:
    	print(evt['message'])
    else:
    	print(json.dumps(evt))

