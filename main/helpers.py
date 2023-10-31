from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from rest_framework.response import Response

from main.models import Order, ResultFile


def generate_zip_of_order_images(order: Order, response: Response):
    in_memory = BytesIO()
    with ZipFile(in_memory, 'w') as zip:  # noqa
        for result_file in order.result_files.all():  # type: ResultFile
            file_name = Path(result_file.file.name).name
            with open(result_file.file.name, 'rb') as f:
                zip.writestr(file_name, data=f.read())

    in_memory.seek(0)
    response.content = in_memory.getvalue()
    in_memory.close()

    return response
