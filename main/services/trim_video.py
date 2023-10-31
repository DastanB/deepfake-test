import os
import ffmpeg

from main.models import SourceFile


class TrimVideoService:
    def __init__(
            self,
            source_file: SourceFile,
            start: int,
            end: int
    ):
        self._source_file = source_file
        self._start = start
        self._end = end

    def trim_video(self):
        path, extension = os.path.splitext(self._source_file.file.name)
        output_path = f'{path}-trimmed{extension}'

        ffmpeg.input(
            self._source_file.file.name,
            ss=self._start,
            to=self._end) \
            .filter('fps', fps=25, round='down') \
            .output(output_path) \
            .run()

        self._source_file.trimmed = output_path
        self._source_file.save()
