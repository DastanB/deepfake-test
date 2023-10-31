import os
import cv2
from pathlib import Path

from django.conf import settings

from main.models import SourceFile


class GetPreviewVideoService:
    def __init__(self, source_file: SourceFile, moment: int, deepfaked: bool):
        self._source_file = source_file
        self._moment = moment
        self._deepfaked = deepfaked

    def _get_output_path(self, name: str, postfix: str):
        path, extension = os.path.splitext(name)
        return f'{path}-{postfix}.jpeg'

    def _set_image(self):
        vidcap = cv2.VideoCapture(self._source_file.file.name)
        vidcap.set(cv2.CAP_PROP_POS_MSEC, self._moment * 1000)
        success, image = vidcap.read()
        if success:
            path = self._get_output_path(self._source_file.file.name, 'preview')
            cv2.imwrite(path, image)

    def get_preview(self):
        self._set_image()
        preview_path = self._get_output_path(self._source_file.file.name, 'preview')
        if self._deepfaked:
            output_destination = self._get_output_path(preview_path, 'modified')
            os.system(
                "{} ./roop/run.py -s {} -t {} -o {} --keep-frames --keep-fps --execution-provider {}"
                .format(
                    settings.PYTHON_PATH, self._source_file.order.target_file.path,
                    preview_path, output_destination, settings.DEEPFAKE_PROVIDER
                )
            )
            enhanced_output_destination = self._get_output_path(output_destination, 'enhanced')
            os.system(
                "{} ./roop/run.py -s {} -t {} -o {} --keep-frames --keep-fps "
                "--frame-processor face_enhancer --execution-provider {}"
                .format(
                    settings.PYTHON_PATH, self._source_file.order.target_file.path,
                    output_destination, enhanced_output_destination, settings.DEEPFAKE_PROVIDER
                )
            )
            self._source_file.preview_deepfaked.name = enhanced_output_destination

        self._source_file.preview.name = preview_path
        self._source_file.save()
