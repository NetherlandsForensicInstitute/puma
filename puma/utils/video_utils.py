import os
import subprocess
from os.path import basename, dirname, isfile
from typing import Optional
from uuid import uuid4

from puma.utils import CACHE_FOLDER, logger, log_error_and_raise_exception

FFMPEG_COMMAND = 'ffmpeg'


def _ffmpeg_is_installed() -> bool:
    completed_process = subprocess.run(f'{FFMPEG_COMMAND} -h', shell=True, capture_output=True)
    return completed_process.returncode == 0 and 'usage: ffmpeg [options]' in completed_process.stdout.decode()


def concat_videos(videos_to_concat, video_path) -> Optional[subprocess.CompletedProcess]:
    """
    A method to concat multiple video into one longer video.
    This can be useful when recording multiple actions, or when recording a video longer than the duration limit allows.

    :param videos_to_concat: The list of video files to concatenate
    :param video_path: the desired output path
    :return: the CompletedProcess for the FFMPEG command
    """
    if videos_to_concat is None or len(videos_to_concat) == 0:
        logger.error(f'Cannot concat videos: no videos provided!')
        return None
    # create folder for output file if needed
    if dirname(video_path):
        os.makedirs(dirname(video_path), exist_ok=True)
    concat_list = f'{CACHE_FOLDER}/{uuid4()}-ffmpegconcatlist.txt'
    try:
        # to concat videos ffmpeg needs an input file with all videos to concat on separate lines
        with open(concat_list, 'w') as file:
            file.write('\n'.join([f"file '{video}'" for video in videos_to_concat]))
        # ffmpeg command
        command = f'{FFMPEG_COMMAND} -f concat -safe 0 -i {concat_list} -c copy {video_path}'
        logger.info(f'Running ffmpeg with command: {command}')
        return subprocess.run(command, shell=True, capture_output=True)
    finally:
        pass
        if os.path.isfile(concat_list):
            os.remove(concat_list)


def stitch_video_horizontal(video_files: [str], output_path: str) -> subprocess.CompletedProcess:
    """
    A method to stitch videos together horizontally using ffmpeg.
    This can be useful when you want to record the screens of multiple devices, and you want to stitch multiple
    recordings together.

    Make sure ffmpeg is installed. By default the command 'ffmpeg' is used. If ffmpeg is not on your path, you need to
    set the path to the ffmpeg binary by setting the video_stitch.FFMPEG_COMMAND string.

    :param video_files: The video files to be stitched
    :param output_path: the path to the output file
    :return: the CompletedProcess for the FFMPEG command
    """
    if video_files is None or len(video_files) < 2:
        log_error_and_raise_exception(logger, f'Expected at least 2 videos to stitch together, got: {video_files}')
    for video_file in video_files:
        if not isfile(video_file):
            log_error_and_raise_exception(logger, f'given video file {video_file} does not exist')
    if not output_path:
        log_error_and_raise_exception(logger, f'Expected a valid output path, got {output_path}')

    logger.info(f'Stitching videos together horizontally: videos {[basename(f) for f in video_files]} into output '
                f'file {output_path}')
    # create folder for output file if needed
    os.makedirs(dirname(output_path), exist_ok=True)
    # check if ffmpeg is installed
    if not _ffmpeg_is_installed():
        log_error_and_raise_exception(logger, 'ffmpeg not installed, please install ffmpeg and add it to the path')
    # create ffmpeg command
    video_arguments = ' '.join([f'-i "{video_file}"' for video_file in video_files])
    command = f'{FFMPEG_COMMAND} -y {video_arguments} -filter_complex hstack=inputs={len(video_files)} "{output_path}"'
    logger.info(f'Running ffmpeg with command: {command}')
    return subprocess.run(command, shell=True, capture_output=True)
