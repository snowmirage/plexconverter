import subprocess
from pprint import pprint as pp
import json
import os

print_prefix = '<plextool.py>     '


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

# Need to look at each video in collection and figure out "Is it too big"

# "Good" Video
# /media/unraid-media/Movies/Pay It Forward (2000)/Pay It Forward 2000 WEBDL-1080p.mkv
# ~ 2h movie its already h264 and it is 4.8 GB ish
# This is perfectly acceptable
# how many bytes is that per second?
# 7404 seconds
# 4987245321 bytes
# 673587.969 Bytes per second
# 673 KB per second

# "Bad" Example
# /media/unraid-media/Movies/The Equalizer 2 (2018)/The Equalizer 2 2018 Remux-2160p.mkv
# ~2h movie its hevc and its 46GB ish
# This is way to big
# 7257 seconds
# 47740263775 bytes
# 6578512.3 Bytes per second
# 6,578,512
# 6 MB per second

# 1 MB per second a 2hr movie would be 7200 MB or 7 GB
# 1000 Bytes per second or already in h264 or h265 is acceptable


plex_library_movie_path = '/media/unraid-media/Movies/'
plex_library_tv_path = '/media/unraid-media/tvshows/'
#plex_library_movie_path ='/media/unraid-media/tvshows/Good Eats/Season 2/'
# plex_library_movie_path = '/media/unraid-media/tvshows/Supergirl/Season 2/'
# movie_library_path = '/media/unraid-media/tvshows/Last Week Tonight with John Oliver'
files_to_process = []
list_video_extentions = [
    '.avi',
    '.divx',
    '.flv',
    '.m4v',
    '.mkv',
    '.mov',
    '.mpg',
    '.mpeg',
    '.wmv',
    '.m2ts',
    '.mp4'
]

list_of_files_not_processed = []
# Get a list of movie files to process and and list of file to not process (not valid video extensions)
for root, subdirs, files in os.walk(plex_library_movie_path):
    for file in files:
        full_file_path = os.path.join(root, file)
        fileName, fileExtention = os.path.splitext(full_file_path)
        if fileExtention.lower() in list_video_extentions:
            print print_prefix + 'Adding: %s' % full_file_path
            files_to_process.append(full_file_path)
        else:
            print print_prefix + 'NOT Adding: %s' % full_file_path
            list_of_files_not_processed.append(full_file_path)

# # Get a list of tvshow files to process and and list of file to not process (not valid video extensions)
for root, subdirs, files in os.walk(plex_library_tv_path):
    for file in files:
        full_file_path = os.path.join(root, file)
        fileName, fileExtention = os.path.splitext(full_file_path)
        if fileExtention.lower() in list_video_extentions:
            print print_prefix + 'Adding: %s' % full_file_path
            files_to_process.append(full_file_path)
        else:
            print print_prefix + 'NOT Adding: %s' % full_file_path
            list_of_files_not_processed.append(full_file_path)



video_meta_data_all_videos = []
video_files_unknown_meta_data = []
for video_file in files_to_process:
    video_meta_data = get_video_meta_data(video_file)
    if video_meta_data != {}:
        print print_prefix + 'This video had valid meta data: %s' % video_file
        video_meta_data_all_videos.append(video_meta_data)
    else:
        print print_prefix + 'This video DID NOT have valid meta data: %s' % video_file
        video_files_unknown_meta_data.append(video_file)

print print_prefix + 'Following is a list of files we found that were not one of our valid video extentions'
pp(list_of_files_not_processed)
print print_prefix + 'Following is a list of video files we could not get metadata for'
pp(video_files_unknown_meta_data)
#pp(video_meta_data_all_movies)

# Lets investigate our data
mega_byte_rate_limit = 3
rate_limit_area_over_MB_per_second = (1920 * 1080) / 3
# video area / MB/s rate limit = mega_byte_by_area_rate_limit
# for 1920x1080 at 3MB/s that should be 691200
total_videos_found = len(video_meta_data_all_videos)
num_videos_in_h265 = 0
num_videos_not_h265_and_over_area_rate_limit = 0
num_videos_not_h265_and_over_area_rate_limit_and_over_3GB = 0

list_of_videos_to_process = []
for video_meta_data in video_meta_data_all_videos:
    if 'hevc' in video_meta_data['video_codecs']:
        num_videos_in_h265 += 1
    else:
        if video_meta_data['area_over_MB_per_second_ratio'] > rate_limit_area_over_MB_per_second:
            num_videos_not_h265_and_over_area_rate_limit += 1
            if video_meta_data['size_MB'] > 3000:
                num_videos_not_h265_and_over_area_rate_limit_and_over_3GB += 1
                list_of_videos_to_process.append(video_meta_data)

print 'Total Videos: %s' % total_videos_found
print 'Videos already h265t: %s' % num_videos_in_h265
print 'Videos over area rate limit and not h265: %s' % num_videos_not_h265_and_over_area_rate_limit
print 'Videos over area rate limit and not h265 and over 3GB: %s' % num_videos_not_h265_and_over_area_rate_limit_and_over_3GB
# need to come up with a combined limit of MB/s of video and video size
# so 3MB/s at 1920x1080
# 2073600 area
# 2073600 / 3 MB
# 691200 per 1 MB /s


# at 1920x1080  which is an area of 2073600
# each second of video can be up to 3MB /s

# to see if a video is "too big"
# file size / duration in seconds = MB /s

# ratio of MB/s to area
# MB/s
# _____  =  _____
# area

# if a video is NOT already h265
# and
# that video has an area_over_MB_per_second_ratio > rate_limit_area_over_MB_per_second
# Then it should be reprocessed into h265

#

# Get a list of everything to process allow you to break out that list in to 3 parts or more
# Script 1 generates the lists of things to process, outputs to files with a config number of breaks
# if breaks is 3 then 3 files   processor_1   processor_2 etc.

# 2nd script takes its "name" looks for its file.
# Gets meta data on existing video
# processes to local dir
# if successful
# deletes original verifies its gone
# Then copies new file to orignal name and location
# Reports on change in file size
# writes log to processor_1 file


# Total Videos: 12058
# Videos already h265t: 587
# Videos over area rate limit and not h265: 11279

# Take your list1
num_videos_per_work_file = 5
current_video_count = 0
current_video_list = []
work_file_number = 1

for video in list_of_videos_to_process:
    if len(current_video_list) < num_videos_per_work_file:
        # if our current video list is less than the number we want per work file add this video
        current_video_list.append(video)
    else:
        # if our current video list is long enough write the list out to our file
        os.mkdir('/media/unraid-media/plexconverter-workingdir/worker-%s' % work_file_number)

        with open('/media/unraid-media/plexconverter-workingdir/worker-%s/worker-%s-list.txt' % (work_file_number, work_file_number), 'w') as fout:
            json.dump(current_video_list, fout)

        current_video_list = []
        current_video_list.append(video)
        work_file_number += 1

if len(current_video_list) > 0:
    # if our current video list is long enough write the list out to our file
    os.mkdir('/media/unraid-media/plexconverter-workingdir/worker-%s' % work_file_number)

    with open('/media/unraid-media/plexconverter-workingdir/worker-%s/worker-%s-list.txt' % (work_file_number, work_file_number), 'w') as fout:
        json.dump(current_video_list, fout)
