from typing import Any, List, Callable
import cv2
import threading
import numpy
import onnxruntime
from gfpgan.utils import GFPGANer

import roop.globals
import roop.processors.frame.core
from roop.core import update_status
from roop.face_analyser import get_many_faces
from roop.typing import Frame, Face
from roop.utilities import conditional_download, resolve_relative_path, is_image, is_video

FACE_ENHANCER = None
THREAD_SEMAPHORE = threading.Semaphore()
THREAD_LOCK = threading.Lock()
NAME = 'ROOP.FACE-ENHANCER'


def get_face_enhancer() -> Any:
    global FACE_ENHANCER

    with THREAD_LOCK:
        if FACE_ENHANCER is None:
            model_path = resolve_relative_path('../models/GFPGANv1.4.onnx')
            FACE_ENHANCER = onnxruntime.InferenceSession(
                model_path,
                providers=roop.globals.execution_providers
            )
    return FACE_ENHANCER


def get_device() -> str:
    if 'CUDAExecutionProvider' in roop.globals.execution_providers:
        return 'cuda'
    if 'CoreMLExecutionProvider' in roop.globals.execution_providers:
        return 'mps'
    return 'cpu'


def clear_face_enhancer() -> None:
    global FACE_ENHANCER

    FACE_ENHANCER = None


def pre_check() -> bool:
    download_directory_path = resolve_relative_path('../models/')
    conditional_download(download_directory_path,
                         ['https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth'])
    return True


def pre_start() -> bool:
    if not is_image(roop.globals.target_path) and not is_video(roop.globals.target_path):
        update_status('Select an image or video for target path.', NAME)
        return False
    return True


def post_process() -> None:
    clear_face_enhancer()


def ffhq_align_crop(img, landmark):
    ffhq_template = numpy.array([
        [192.98138, 239.94708], [318.90277, 240.1936],
        [256.63416, 314.01935], [201.26117, 371.41043],
        [313.08905, 371.15118]
    ], dtype=numpy.float32)
    affine_matrix = cv2.estimateAffinePartial2D(landmark, ffhq_template, method=cv2.LMEDS)[0]
    cropped_face = cv2.warpAffine(img, affine_matrix, (512, 512), borderMode=cv2.BORDER_CONSTANT,
                                  borderValue=(135, 133, 132))

    return cropped_face, affine_matrix


def enhance_face(target_face: Face, temp_frame: Frame) -> Frame:
    face_enhancer = get_face_enhancer()
    temp_face, matrix = ffhq_align_crop(temp_frame, target_face['kps'])
    temp_face = temp_face.astype(numpy.float32)[:, :, ::-1] / 255.0
    temp_face = (temp_face - 0.5) / 0.5
    temp_face = numpy.expand_dims(temp_face.transpose(2, 0, 1), axis=0).astype(numpy.float32)

    with THREAD_SEMAPHORE:
        temp_face = face_enhancer.run(None, {face_enhancer.get_inputs()[0].name: temp_face})[0][0]

    temp_face = numpy.clip(temp_face, -1, 1)
    temp_face = (temp_face + 1) / 2
    temp_face = temp_face.transpose(1, 2, 0)
    temp_face = (temp_face * 255.0).round()
    temp_face = temp_face.astype(numpy.uint8)[:, :, ::-1]

    inverse_affine = cv2.invertAffineTransform(matrix)
    h, w = temp_frame.shape[0:2]
    face_h, face_w = temp_face.shape[0:2]
    inv_restored = cv2.warpAffine(temp_face, inverse_affine, (w, h))
    mask = numpy.ones((face_h, face_w, 3), dtype=numpy.float32)
    inv_mask = cv2.warpAffine(mask, inverse_affine, (w, h))
    inv_mask_erosion = cv2.erode(inv_mask, numpy.ones((2, 2), numpy.uint8))
    inv_restored_remove_border = inv_mask_erosion * inv_restored
    total_face_area = numpy.sum(inv_mask_erosion) // 3
    w_edge = int(total_face_area ** 0.5) // 20
    erosion_radius = w_edge * 2
    inv_mask_center = cv2.erode(inv_mask_erosion, numpy.ones((erosion_radius, erosion_radius), numpy.uint8))
    blur_size = w_edge * 2
    inv_soft_mask = cv2.GaussianBlur(inv_mask_center, (blur_size + 1, blur_size + 1), 0)
    temp_frame = inv_soft_mask * inv_restored_remove_border + (1 - inv_soft_mask) * temp_frame
    temp_frame = temp_frame.clip(0, 255).astype('uint8')

    return temp_frame


def process_frame(source_face: Face, reference_face: Face, temp_frame: Frame) -> Frame:
    many_faces = get_many_faces(temp_frame)
    if many_faces:
        for target_face in many_faces:
            temp_frame = enhance_face(target_face, temp_frame)
    return temp_frame


def process_frames(source_path: str, temp_frame_paths: List[str], update: Callable[[], None]) -> None:
    for temp_frame_path in temp_frame_paths:
        temp_frame = cv2.imread(temp_frame_path)
        result = process_frame(None, None, temp_frame)
        cv2.imwrite(temp_frame_path, result)
        if update:
            update()


def process_image(source_path: str, target_path: str, output_path: str) -> None:
    target_frame = cv2.imread(target_path)
    result = process_frame(None, None, target_frame)
    cv2.imwrite(output_path, result)


def process_video(source_path: str, temp_frame_paths: List[str]) -> None:
    roop.processors.frame.core.process_video(None, temp_frame_paths, process_frames)
