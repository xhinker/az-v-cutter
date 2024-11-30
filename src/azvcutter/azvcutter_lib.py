#%%
import subprocess
import os
import sys
import subprocess
import shutil
import tempfile
from typing import List, Tuple, Optional

def apply_video_effect(
    video_path: str
    , operation: str    = "hflip"
    , preset: str       = "fast"
    , audio_codec: str  = "aac"
) -> None:
    """
    Applies a specified video effect to the input video using ffmpeg.

    Args:
    - video_path (str): Path to the input video file.
    - operation (str, optional): Effect to apply. Defaults to "hflip".
        Supported operations:
            - "hflip": Horizontal flip
            - "vflip": Vertical flip
            - "180rotate": Rotate by 180 degrees
    - preset (str, optional): Encoding preset for h264_nvenc. Defaults to "fast".
    - audio_codec (str, optional): Audio codec for the output. Defaults to "aac".

    Raises:
    - KeyError: If the specified operation is not supported.
    - RuntimeError: If ffmpeg is not found in the system's PATH.
    """

    # Define supported operations and their corresponding ffmpeg filters
    operation_definitions = {
        # **Flipping**
        "hflip": "hflip",  # Horizontal flip
        "vflip": "vflip",  # Vertical flip

        # **Rotation**
        "180rotate": "rotate=180*PI/180",  # Rotate by 180 degrees
        "90clockwise": "rotate=90*PI/180",  # Rotate 90 degrees clockwise
        "90counterclk": "rotate=-90*PI/180",  # Rotate 90 degrees counter-clockwise

        # **Scaling**
        "scalehd": "scale=-1:1080",  # Scale to HD (1080p) while maintaining aspect ratio
        "scalesd": "scale=-1:480",   # Scale to SD (480p) while maintaining aspect ratio
        "scalecustom": "scale={width}:{height}",  # **CUSTOM**: Replace `{width}` and `{height}` when selecting this option

        # **Cropping**
        "crop16x9": "crop=iw*16/9:ih*(16/9)*(iw/iw)",  # Crop to 16:9 aspect ratio
        "crop4x3": "crop=iw*4/3:ih*(4/3)*(iw/iw)",    # Crop to 4:3 aspect ratio
        "cropcustom": "crop={width}:{height}:{x}:{y}",  # **CUSTOM**: Replace `{width}`, `{height}`, `{x}`, and `{y}` when selecting this option

        # **Padding**
        "pad16x9": "pad=(iw*16/9):ih:(ow-iw)/2:(oh-ih)/2:color=black",  # Pad to 16:9 aspect ratio
        "pad4x3": "pad=(iw*4/3):ih:(ow-iw)/2:(oh-ih)/2:color=black",    # Pad to 4:3 aspect ratio
        "padcustom": "pad={width}:{height}:{x}:{y}:color={color}",       # **CUSTOM**: Replace `{width}`, `{height}`, `{x}`, `{y}`, and `{color}` when selecting this option

        # **Other Effects**
        "grayscale": "hue=s=0",  # Convert to grayscale
        "invert": "negate",      # Invert colors
        "blur": "boxblur=2:2"    # Apply a blur effect
    }

    # Validate the chosen operation
    if operation not in operation_definitions:
        raise KeyError(f"Unsupported operation: '{operation}'. Supported operations: {list(operation_definitions.keys())}")

    # Check if ffmpeg is available
    if not shutil.which('ffmpeg'):
        raise RuntimeError("FFmpeg is not found. Please install FFmpeg and ensure it's in the system's PATH.")

    # Derive output video path by appending the operation name to the input path
    path_without_extension, video_extension_with_dot = os.path.splitext(video_path)
    output_video_path = f"{path_without_extension}_{operation}{video_extension_with_dot}"

    # Construct ffmpeg command with user-specified settings
    ffmpeg_command = [
        "ffmpeg"
        , "-i", video_path
        , "-vf", operation_definitions[operation]
        , "-c:a", audio_codec
        , "-c:v", "h264_nvenc"
        , "-preset", preset
        , output_video_path
    ]

    # Display the constructed command for transparency/debugging
    print(ffmpeg_command)

    # Execute the ffmpeg command
    try:
        subprocess.run(ffmpeg_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg execution failed with return code {e.returncode}")
        raise

def cut_video(video_path: str, cutoff_ranges: List[Tuple[str, str]]) -> None:
    """
    Cuts specified ranges from a video using ffmpeg with h264_nvenc encoder.

    :param video_path: Path to the input video file.
    :param cutoff_ranges: List of tuples containing start and end timestamps (HH:MM:SS.SS) to be cut off.
                           Use 'inf' as the end timestamp to represent the end of the video.
    """

    # Check if ffmpeg is available
    if not shutil.which('ffmpeg'):
        raise RuntimeError("FFmpeg is not found. Please install FFmpeg and ensure it's in the system's PATH.")

    # Create a temporary directory for intermediate files
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Split the video into segments based on the keep ranges (inverted logic)
        keep_ranges = []
        if cutoff_ranges[0][0] != '00:00:00.00':
            keep_ranges.append(('00:00:00.00', cutoff_ranges[0][0]))
        for i in range(len(cutoff_ranges)):
            if cutoff_ranges[i][1] != 'inf':
                keep_ranges.append((cutoff_ranges[i][1], 'inf' if i == len(cutoff_ranges) - 1 else cutoff_ranges[i+1][0]))
        
        # Generate segment files
        segment_files = []
        for i, (start, end) in enumerate(keep_ranges):
            output_file = f"{tmp_dir}/segment_{i}.mp4"
            cmd = [
                'ffmpeg', '-i', video_path,
                '-ss', start, 
                '-to', end if end != 'inf' else '',  # Omitting end for 'inf'
                '-c:v', 'h264_nvenc',
                output_file
            ]
            if end == 'inf':  # Remove the option if end time is 'inf'
                cmd.remove('-to')
                cmd.remove('')
            subprocess.run(cmd, check=True)
            segment_files.append(output_file)

        # Concatenate the segments
        concat_file = f"{tmp_dir}/concat.txt"
        with open(concat_file, 'w') as f:
            for file in segment_files:
                f.write(f"file '{file}'\n")
        
        # Final output file path (same name as input but with "_output" appended before extension)
        filename, file_extension = video_path.rsplit('.', 1)
        output_path = f"{filename}_output.{file_extension}"
        
        # Concatenate and write to final output
        concat_cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_file,
            '-c:v', 'h264_nvenc', '-c:a', 'copy',  # Assuming audio copy is fine; adjust if needed
            output_path
        ]
        subprocess.run(concat_cmd, check=True)

    print(f"Video with cut ranges has been saved to: {output_path}")
    
def extract_sub_video(
    source_video_path: str, 
    start_time: str, 
    end_time: Optional[str] = 'inf'
) -> None:
    """
    Extracts a sub-video from a source video using ffmpeg.

    :param source_video_path: Path to the source video file.
    :param start_time: Start time of the sub-video in HH:MM:SS.SS format.
    :param end_time: End time of the sub-video. Defaults to 'inf' for the end of the video.
    """

    # Check if ffmpeg is available
    if not shutil.which('ffmpeg'):
        raise RuntimeError("FFmpeg is not found. Please install FFmpeg and ensure it's in the system's PATH.")

    # Determine output file path (appending '_sub' before the extension)
    filename, file_extension = os.path.splitext(source_video_path)
    output_path = f"{filename}_sub{file_extension}"

    # Construct ffmpeg command
    cmd = [
        'ffmpeg', '-i', source_video_path,
        '-ss', start_time,  # Start time
    ]
    
    if end_time.lower() != 'inf':
        cmd.extend(['-to', end_time])  # End time if not 'inf'

    cmd.extend([
        '-c:v', 'h264_nvenc',  # Using h264_nvenc encoder; adjust based on your HW
        '-c:a', 'copy',  # Copying audio stream; adjust encoding if necessary
        output_path
    ])

    # Execute ffmpeg command
    subprocess.run(cmd, check=True)

    print(f"Sub-video extracted and saved to: {output_path}")

def merge_videos(
    video_files
    , output_file
    , concate_only  = True
    , preset        = "p1"
    , audio_codec   = "aac"
    , fps           = 30
    , bitrate       = "8M"
):
    """
    Merges multiple video files into one using FFmpeg with h264_nvenc encoder.

    :param video_files: List of paths to input video files.
    :param output_file: Path to the desired output MP4 file.
    :param preset: Quality preset for h264_nvenc (default: "slow").
    :param audio_codec: Audio codec for output (default: "aac").
    """
    if not video_files:
        print("No video files provided.")
        return

    if not all(os.path.isfile(file) for file in video_files):
        print("One or more input files do not exist.")
        return

    # Create a text file listing all input files for concat demuxer
    list_file = 'video_list.txt'
    with open(list_file, 'w') as f:
        for file in video_files:
            f.write(f"file '{file}'\n")

    if concate_only:
        ffmpeg_command = [
            "ffmpeg"
            , "-f", "concat"                # Input format for concat demuxer
            , "-safe", "0"                  # Reduce security restrictions
            , "-i", list_file               # Input is our list file
            , "-c", "copy"                  # copy data instead of encoding
            , output_file                   # Output file path
        ]
    else:
        # FFmpeg command using concat demuxer and h264_nvenc encoder
        # Note: Since we're using a list file, the input (-i) is the list file itself
        ffmpeg_command = [
            "ffmpeg"
            , "-f", "concat"                # Input format for concat demuxer
            , "-safe", "0"                  # Reduce security restrictions
            , "-i", list_file               # Input is our list file
            , "-c:v", "h264_nvenc"          # Video codec
            , "-preset", preset             # Preset for quality/performance
            , "-c:a", audio_codec           # Audio codec
            , "-b:a", "128k"                # Bitrate for audio (optional, adjust as needed)
            , "-movflags", "+faststart"     # For faster streaming start
            , "-r", f"{fps}"                # set fps
            , "-b:v", bitrate               # set bit rate
            , output_file                   # Output file path
        ]

    # Execute FFmpeg command
    try:
        subprocess.run(ffmpeg_command, check=True)
        print(f"Videos merged successfully to: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

    finally:
        # Clean up the temp list file
        if os.path.exists(list_file):
            os.remove(list_file)