import os
from pprint import pprint as pp
import ast
import json

worker_file_full_path = '/media/unraid-media/plexconverter-workingdir/worker-1/worker-1-list.txt'

# Read our list of videos to process from our file
with open(worker_file_full_path) as json_file:
    data = json.load(json_file)

print data[0]['size_MB']
