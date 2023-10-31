import os
from pathlib import Path

from django.conf import settings

from main.models import Order, ResultFile


class ExecuteOrderService:
    def __init__(self, order: Order):
        self._order = order

    def _process_order(self):
        for source_file in self._order.source_files.all():
            output_destination = f'./static/results/{source_file.id}-modified{Path(source_file.file.path).suffix}'
            os.system(
                "{} ./roop/run.py -s {} -t {} -o {} --keep-frames --keep-fps --execution-provider {}"
                .format(
                    settings.PYTHON_PATH, source_file.order.target_file.path,
                    source_file.file.path, output_destination, settings.DEEPFAKE_PROVIDER
                )
            )
            enhanced_output_destination = f'./static/results/{source_file.id}-' \
                                          f'modified-enhanced{Path(source_file.file.path).suffix}'
            os.system(
                "{} ./roop/run.py -s {} -t {} -o {} --keep-frames --keep-fps "
                "--frame-processor face_enhancer --execution-provider {}"
                .format(
                    settings.PYTHON_PATH, source_file.order.target_file.path,
                    output_destination, enhanced_output_destination, settings.DEEPFAKE_PROVIDER
                )
            )

            result_file = ResultFile.objects.create(
                order=self._order
            )
            result_file.file.name = enhanced_output_destination
            result_file.save()

            path, extension = os.path.splitext(source_file.file.name)
            source_file.face = f'{path}-face{extension}'
            source_file.save()

            os.remove(output_destination)

    def run(self):
        self._process_order()
