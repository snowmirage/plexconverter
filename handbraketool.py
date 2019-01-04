import os
import argparse
from pprint import pprint as pp
import subprocess
import shutil
import sys
import errno

########
# Requires the HandBrakeCLI to be installed on a linux system, note the spelling and caps here which seemed odd to me
# but was correct
# Also requires the hardcoded myh265.json handbrake settings exported of the profile named myh265
# This will search all nested dir under the watch dir for video files of the "list_video_extentions" types
# Add all those files to a list
# Create matching paths in the output dir
# Re-encode the source file
# Then if successful delete the original source file and its paths (anything below Movies or Series)

arg_parser = argparse.ArgumentParser(description='soemthing')
arg_parser.add_argument('watch_dir', help='full path to a directory we should watch for videos')
arg_parser.add_argument('output_dir', help='full path to a directory we should output videos')
args = arg_parser.parse_args()
# args.watch_dir = "/run/user/1000/gvfs/smb-share:server=192.168.0.216,share=downloads/desktop_handbrake_watch"
# args.output_dir = "/run/user/1000/gvfs/smb-share:server=192.168.0.216,share=downloads/desktop_handbrake_output"
# args.watch_dir = "/media/unraid-downloads/desktop_handbrake_watch"
# args.output_dir = "/media/unraid-downloads/desktop_handbrake_output"
# cp = subprocess.Popen(['touch', '/run/user/1000/gvfs/smb-share:server=192.168.0.216,share=downloads/desktop_handbrake_watch/write_test.txt'])
# cp = subprocess.Popen(['touch', '/run/user/1000/gvfs/smb-share:server=192.168.0.216,share=downloads/desktop_handbrake_output/write_test.txt'])
# raw_input('etner')
list_video_extentions = [
    '.avi',
    '.divx',
    '.flv',
    '.m4v',
    '.mkv',
    '.mov',
    '.mpg',
    '.mpeg',
    '.wmv'
]
print_prefix = '<handbraketool.py>          '
print print_prefix + 'watch-dir: %s' % args.watch_dir
print print_prefix + 'output-dir: %s' % args.output_dir
files_to_proecess = []

for root, subdirs, files in os.walk(args.watch_dir):
    for file in files:
        full_file_path = os.path.join(root, file)
        fileName, fileExtention = os.path.splitext(full_file_path)
        if fileExtention.lower() in list_video_extentions:
            print print_prefix + 'Adding: %s' % full_file_path
            files_to_proecess.append(full_file_path)


for video_file in files_to_proecess:
    print print_prefix + 'Processing file: %s' % video_file
    video_conversion_success = False
    # Get the directory structure within the watch folder
    sub_dir_structure_with_file = video_file.split(args.watch_dir, 1)[1].rsplit('/', 1)
    sub_dir_structure = sub_dir_structure_with_file[0]
    file_name = sub_dir_structure_with_file[1]
    output_file_path = args.output_dir + sub_dir_structure + '/' + file_name

    # debug override files
    # video_file = '/media/unraid-downloads/desktop_handbrake_watch/Movies/vid.webm'
    # output_file_path = '/media/unraid-downloads/desktop_handbrake_output/Movies/file.mkv'

    # Before running our command make sure the full directory structure exists
    try:
        os.makedirs(output_file_path.rsplit('/', 1)[0])
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(output_file_path.rsplit('/', 1)[0]):
            pass
        else:
            raise

    cmd_profile = ['HandBrakeCLI', '--preset-import-file', './myh265.json', '-Z', 'myh265', '-i', video_file, '-o', output_file_path]
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
    video_conversion_success = True
    if video_conversion_success:
        print print_prefix + 'HandBrake Video Processing Appears to have completed Successfully for file: %s' % video_file
    else:
        print print_prefix + 'HandBrake Video Process Appears to have failed for file: %s' % video_file

    # debug tree delete override
    # video_conversion_success = False

    # When the handbrake process ends delete the original file's folder
    if '/Series/' in video_file:
        dir_to_delete = args.watch_dir + '/Series/' + video_file.split('/Series/', 1)[1].split('/', 1)[0]
    elif '/Movies/' in video_file:
        dir_to_delete = args.watch_dir + '/Movies/' + video_file.split('/Movies/', 1)[1].split('/', 1)[0]
    else:
        dir_to_delete = video_file
    if video_conversion_success:
        if os.path.isdir(dir_to_delete):
            print print_prefix + 'Video Processing succeeded deleting original dir tree: %s' % dir_to_delete
            shutil.rmtree(dir_to_delete)
        else:
            print print_prefix + 'Video Processing succeeded deleting original file: %s' % dir_to_delete
            os.remove(dir_to_delete)

    raw_input('asdkjflas;jfkla;dsjfl;k')