import os
from pprint import pprint as pp
import ast
import json
import subprocess
import sys
from shutil import copyfile

# sudo add-apt-repository ppa:stebbins/handbrake-releases
# sudo apt-get update
# sudo apt-get install handbrake-gtk handbrake-cli


print_prefix = '<plexconverterworker.py>     '
worker_file_full_path = '/media/unraid-media/plexconverter-workingdir/worker-1/worker-1-list.txt'

# Read our list of videos to process from our file
with open(worker_file_full_path) as json_file:
    data = json.load(json_file)

worker_working_path = worker_file_full_path.rsplit('/', 1)[0]

for video_file in data:
    video_conversion_success = False
    print print_prefix + 'Video to be processed: %s' % video_file['filename']
    temp_output_path = worker_working_path + '/' + video_file['filename'].rsplit('/', 1)[1]
    print print_prefix + 'Temp video path: %s' % temp_output_path
    cmd_profile = ['HandBrakeCLI', '--preset-import-file', './myh265.json', '-Z', 'myh265', '-i', video_file['filename'], '-o', temp_output_path]
    print print_prefix + 'Running HandBrake cmd: %s' % ' '.join(cmd_profile)
    cp = subprocess.Popen(cmd_profile, stderr=subprocess.PIPE)
    success_string = 'Encode done!'
    output_char_list = []
    while True:
        out = cp.stderr.read(1)
        if out == '' and cp.poll() is not None:
            break
        if out != '':
            output_char_list.append(out)
            sys.stdout.write(out)
            sys.stdout.flush()
    print print_prefix + 'HandBrake cmd finished'
    output_string = ''.join(output_char_list)
    if success_string in output_string:
        video_conversion_success = True
    if video_conversion_success:
        print print_prefix + 'HandBrake Video Processing Appears to have completed Successfully for file: %s' % video_file['filename']
        # Now that the file has been successfully processed remove the original file
        raw_input('about to remove original')
        os.remove(video_file['filename'])
        # Now copy the new file to the original location
        raw_input('about to copy new')
        copyfile(temp_output_path, video_file['filename'])

        print print_prefix + 'Original File Size: %s New File Size: %s' % (video_file['size'], os.path.getsize(video_file['filename']))

    else:
        print print_prefix + 'HandBrake Video Process Appears to have failed for file: %s' % video_file['filename']
        os.remove(temp_output_path)
    raw_input('Enter to go to next file')
