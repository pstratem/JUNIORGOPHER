#!/usr/bin/env python3
import cv2
import numpy as np
import time, os, os.path, re, uuid, sys

def make_summary_video(segments_path, sorted_segments, summary_path):
    print(F"writing summary video to {summary_path}")
    video_writer = cv2.VideoWriter(summary_path, cv2.CAP_FFMPEG, cv2.VideoWriter_fourcc(*'avc1'), 30, (1920, 1080))
    if not video_writer.isOpened():
        print("failed to open output")
        return
    background_subtractor = cv2.cuda.createBackgroundSubtractorMOG2(history=500, varThreshold = 16, detectShadows = True)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10,10))
    open_filter = cv2.cuda.createMorphologyFilter(cv2.MORPH_OPEN, cv2.CV_8UC1, kernel)
    close_filter = cv2.cuda.createMorphologyFilter(cv2.MORPH_CLOSE, cv2.CV_8UC1, kernel)
    stream = cv2.cuda_Stream()
    frame_gpu = cv2.cuda_GpuMat()

    previous_segment_time = 0
    ignore_next_frame = False

    for segment in sorted_segments:
        # if the segments aren't continuous, reset the background subtractor and ignore the first frame
        if segment - previous_segment_time > 60:
            print("missing segment, background subtractor reset")
            background_subtractor = cv2.cuda.createBackgroundSubtractorMOG2(history=500, varThreshold = 16, detectShadows = True)
            ignore_next_frame = True

        try:
            capture = cv2.cudacodec.createVideoReader(os.path.join(segments_path, F"{segment}.mp4"))
            capture.set(cv2.cudacodec.ColorFormat_BGR)

            while True:
                ret, frame = capture.nextFrame()
                if not ret:
                    break

                frame = cv2.cuda.resize(frame, (1920, 1080))
                resized_frame = frame
                frame_gpu = background_subtractor.apply(frame, -1, None)

                # cant detect motion in the first frame after resetting the background subtractor
                if ignore_next_frame:
                    ignore_next_frame = False
                    continue

                # despeckle
                open_filter.apply(frame_gpu, frame_gpu)
                close_filter.apply(frame_gpu, frame_gpu)

                non_zero = cv2.cuda.countNonZero(frame_gpu)

                if non_zero < 2500:
                    continue

                frame = frame_gpu.download()

                contours, hierarchy = cv2.findContours(frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                motion_threshold = int((frame.shape[0] * 0.05) * (frame.shape[1] * 0.05))
                motion = False
                for contour in contours:
                    contour_area = cv2.contourArea(contour)
                    if contour_area > motion_threshold:
                        motion = True

                if motion:
                    resized_frame = resized_frame.download()
                    video_writer.write(resized_frame)

            # only update this if we actually successfully read the entire segment
            previous_segment_time = segment
        except cv2.error as e:
            print(e)
    video_writer.release()

segment_dir_pattern = re.compile('^(\d+)$')
def list_days(camera_segment_path):
    days = []
    for direntry in os.scandir(camera_segment_path):
        if direntry.is_dir() and segment_dir_pattern.match(direntry.name):
            days.append(direntry.name)
    return days

segment_pattern = re.compile('^(\d+).mp4$')
def list_segments_by_day(day_segment_path):
    segments = []
    for direntry in os.scandir(day_segment_path):
        m = segment_pattern.match(direntry.name)
        if direntry.is_file() and m:
            segments.append(m.group(1))
    return segments

camera_segments_path = "/var/lib/juniorgopher/segments/"

camera_id = uuid.UUID(sys.argv[1])
day = int(sys.argv[2])

camera_segment_path = os.path.join(camera_segments_path, str(camera_id))
day_segment_path = os.path.join(camera_segment_path, str(day))

segments = list_segments_by_day(day_segment_path)
segments = list(map(int, segments))
segments.sort()
summary_path = os.path.join(camera_segment_path, F"summary-{day}.mp4")
make_summary_video(day_segment_path, segments, summary_path)

"""
for direntry in os.scandir(camera_segments_path):
    try:
        camera_id = uuid.UUID(direntry.name)
    except ValueError:
        continue
    camera_segment_path = os.path.join(camera_segments_path, direntry.name)
    days = list_days(camera_segment_path)
    for day in days:
        summary_path = os.path.join(camera_segment_path, F"summary-{day}.mp4")
        if os.path.exists(summary_path):
            continue
        day_segment_path = os.path.join(camera_segment_path, day)
        segments = list_segments_by_day(day_segment_path)
        segments = list(map(int, segments))
        segments.sort()
        make_summary_video(day_segment_path, segments, summary_path)
"""
