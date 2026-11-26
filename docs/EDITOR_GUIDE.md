# Easy Video Editor

## Upload
Select one or more MP4, MOV, MKV or WebM clips and choose **Add selected videos**. The editor stores a working copy in the Kaggle session and shows a local browser preview of the original.

## Trim
Select a clip, set Start and End in seconds, and choose **Trim selected clip**. The backend calculates duration as End minus Start.

## Resize
Choose 480p, 720p, 1080p or Custom. The backend preserves aspect ratio and pads the frame to the selected dimensions.

## Join
Tick at least two clips and choose **Join selected clips**. The backend currently uses FFmpeg concat stream-copy, so the clips should have matching codecs, frame rates, dimensions and stream layouts. Normalize clips to the same output preset if joining fails.

## Preview and download
Every successful operation displays an MP4 preview and a download link. Uploaded originals are not overwritten.
