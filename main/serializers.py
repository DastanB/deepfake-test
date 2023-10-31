import os
import cv2
from PIL import Image

from rest_framework import serializers

from main.models import Order, SourceFile, ResultFile
from main.validators import FileValidator


ALLOWED_IMAGE_EXTENSIONS = ["png", "jpg", "jpeg", "mp4"]


class UploadSourceFilesSerializer(serializers.Serializer):
    source_files = serializers.FileField(
        validators=[FileValidator(
            allowed_extensions=ALLOWED_IMAGE_EXTENSIONS,
            max_size=50*1024*1024,
        )]
    )

    def create(self, validated_data):
        files = self.context['request'].FILES

        source_files = []
        for file in files.getlist('source_files'):
            source_file = SourceFile.objects.create(
                file=file,
            )
            source_files.append(source_file)

        face_cascade = cv2.CascadeClassifier('roop/models/haarcascade_frontalface_alt2.xml')

        for file in source_files:
            if os.path.splitext(file.file.name)[1] not in ['.jpg', '.jpeg', '.png']:
                continue

            img = cv2.imread(file.file.name)

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            for x, y, w, h in faces:
                faces = img[y:y + h, x:x + w]
                path, extension = os.path.splitext(file.file.name)

                cv2.imwrite(f'{path}-face{extension}', faces)
                file.face = f'{path}-face{extension}'
                file.save()

        return source_files

    def update(self, instance, validated_data):
        # Method is not usable
        pass


class UploadTargetFilesSerializer(serializers.Serializer):
    target_file = serializers.FileField(
        validators=[FileValidator(
            allowed_extensions=ALLOWED_IMAGE_EXTENSIONS,
            max_size=50 * 1024 * 1024,
        )]
    )

    def create(self, validated_data):
        files = self.context['request'].FILES
        order = Order.objects.create(target_file=files['target_file'])
        face_cascade = cv2.CascadeClassifier('roop/models/haarcascade_frontalface_alt2.xml')

        target_img = cv2.imread(order.target_file.file.name)
        gray = cv2.cvtColor(target_img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        for x, y, w, h in faces:
            faces = target_img[y:y + h, x:x + w]
            path, extension = os.path.splitext(order.target_file.name)

            cv2.imwrite(f'{path}-face{extension}', faces)
            order.target_face = f'{path}-face{extension}'
            order.save()

        return order

    def update(self, instance, validated_data):
        # Method is not usable
        pass


class UpdateSourceFilesSerializer(serializers.Serializer):
    source_file_ids = serializers.ListSerializer(child=serializers.IntegerField())

    def update(self, instance, validated_data):
        for source_file_id in validated_data['source_file_ids']:
            source_file = SourceFile.objects.get(id=source_file_id)
            source_file.order_id = instance.id
            source_file.save()

        return instance

class TrimFileVideoSerializer(serializers.Serializer):
    start = serializers.IntegerField()
    end = serializers.IntegerField()


class GetPreviewofVideoFileSerializer(serializers.Serializer):
    moment = serializers.IntegerField()


class SourceFileSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()
    face = serializers.SerializerMethodField()
    trimmed = serializers.SerializerMethodField()

    class Meta:
        model = SourceFile
        fields = '__all__'

    def get_file(self, instance):
        return instance.file.name

    def get_face(self, instance):
        return instance.face.name

    def get_trimmed(self, instance):
        return instance.trimmed.name

    def get_preview(self, instance):
        return instance.preview.name

    def get_preview_deepfaked(self, instance):
        return instance.preview_deepfaked.name


class ResultFileSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()

    class Meta:
        model = ResultFile
        fields = '__all__'

    def get_file(self, instance):
        return instance.file.name.replace('./', '')


class OrderRetrieveSerializer(serializers.ModelSerializer):
    source_files = SourceFileSerializer(many=True)
    result_files = ResultFileSerializer(many=True)
    target_file = serializers.SerializerMethodField()
    target_face = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            'id',
            'target_file',
            'target_face',
            'source_files',
            'result_files',
        )

    def get_target_file(self, instance):
        return instance.target_file.name

    def get_target_face(self, instance):
        return instance.target_face.name
