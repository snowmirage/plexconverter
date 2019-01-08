import os
from pprint import pprint as pp
import ast
import json
import subprocess
import sys
from shutil import copyfile
import argparse

arg_parser = argparse.ArgumentParser(description='soemthing')
arg_parser.add_argument('worker_file_full_path', help='full path to a worker file from plexconverter-manager.py')

args = arg_parser.parse_args()

# sudo add-apt-repository ppa:stebbins/handbrake-releases
# sudo apt-get update
# sudo apt-get install handbrake-gtk handbrake-cli


print_prefix = '<plexconverterworker.py>     '
def get_video_meta_data(video_path):
    '''
    Using ffprode get the size, duration and codec used for the given video file, requires ffmpeg to be installed on
    the system
    :param video_path: full path to the file
    :return: dictionary containing size duration codec and filename
    '''
    cmd_list = ['ffprobe', '-show_format', '-show_streams', '-loglevel', 'quiet', '-print_format', 'json', video_path]
    print print_prefix + 'Running cmd: %s' % ' '.join(cmd_list)

    try:
        output = subprocess.check_output(cmd_list)
        jsonoutput = json.loads(output)

    except subprocess.CalledProcessError as e:
        # raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        jsonoutput = {}

    if jsonoutput != {}:
        if 'duration' not in jsonoutput['format']:
            video_meta_data = {}
        else:
            #pp(jsonoutput)
            video_meta_data = {}
            video_meta_data['size'] = jsonoutput['format']['size']
            video_meta_data['size_MB'] = float(video_meta_data['size']) / 1000 / 1000
            video_meta_data['duration'] = jsonoutput['format']['duration']

            list_video_streams = []
            video_codec_list = []
            video_codec_long_name_list = []
            for stream in jsonoutput['streams']:
                if stream['codec_type'] == 'video':
                    list_video_streams.append(stream)

            if len(list_video_streams) < 1:
                print print_prefix + 'ffprobe doesnt seem to think this video file has any video streams'
                pp(jsonoutput)
                exit(1)
            max_video_height = 0
            max_video_width = 0
            # many videos have multiple sizes for all the streams lets find the largest and use that
            for video_stream in list_video_streams:
                video_codec_list.append(video_stream['codec_name'])
                video_codec_long_name_list.append(video_stream['codec_long_name'])
                if 'coded_height' in video_stream:
                    if video_stream['coded_height'] > max_video_height:
                        max_video_height = video_stream['coded_height']
                        if 'coded_width' in video_stream:
                            max_video_width = video_stream['coded_width']

            video_codec_list = list(set(video_codec_list))

            # there must have been only one video stream
            video_meta_data['video_codecs'] = video_codec_list
            video_meta_data['video_codecs_long_name'] = video_codec_long_name_list
            video_meta_data['filename'] = jsonoutput['format']['filename']
            video_meta_data['bytes_per_second'] = float(video_meta_data['size']) / float(video_meta_data['duration'])
            video_meta_data['MB_per_second'] = video_meta_data['bytes_per_second'] / 1000 / 1000
            video_meta_data['height'] = max_video_height
            video_meta_data['width'] = max_video_width
            video_meta_data['area'] = max_video_height * max_video_width
            video_meta_data['area_over_MB_per_second_ratio'] = video_meta_data['area'] / video_meta_data['MB_per_second']
            # pp(jsonoutput)
            # raw_input('Enter to continue')
    else:
        video_meta_data = {}
    return video_meta_data

worker_file_full_path = args.worker_file_full_path

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
        print print_prefix + 'HandBrake Video Processing Appears to have completed Successfully for file: %s' % video_file['filename']
        print print_prefix + 'Before assuming the conversion was successful we will verify the duration of the new file appears correct'
        print print_prefix + 'Stats of original file'
        pp(video_file)
        new_video_meta_data = get_video_meta_data(temp_output_path)
        print print_prefix + 'Stats of new file'
        pp(new_video_meta_data)
        if video_file['duration'] == new_video_meta_data['duration']:
            print print_prefix + 'The duration of the new file appears to match the old success!'
            video_conversion_success = True

    if video_conversion_success:
        # Now that the file has been successfully processed remove the original file
        print print_prefix + 'Removing the original file: %s' % video_file['filename']
        try:
            os.remove(video_file['filename'])
        except OSError:
            pass

        # Now copy the new file to the original location
        print print_prefix + 'Copying the new file to the original file location: cp %s %s' % (temp_output_path, video_file['filename'])
        copyfile(temp_output_path, video_file['filename'])

        # Now remove the temp file
        print print_prefix + 'Removing the temp video file: %s' % temp_output_path
        try:
            os.remove(video_file['filename'])
        except OSError:
            pass
        
        print print_prefix + 'Original File Size: %s New File Size: %s' % (video_file['size'], os.path.getsize(video_file['filename']))

    else:
        print print_prefix + 'HandBrake Video Process Appears to have failed for file: %s' % video_file['filename']
        try:
            os.remove(temp_output_path)
        except OSError:
            pass
