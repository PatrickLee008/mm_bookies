from google.cloud import vision
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(r'D:\Codes\Soccer2_App_Server\vision-391109-c5e81ff13cf1.json')


def detect_text(path):
    """Detects text in the file."""

    client = vision.ImageAnnotatorClient(credentials=credentials)
    # client = vision.ImageAnnotatorClient()

    with open(path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    print("Texts:")

    for text in texts:
        print(f'\n"{text.description}"')

        vertices = [
            f"({vertex.x},{vertex.y})" for vertex in text.bounding_poly.vertices
        ]

        print("bounds: {}".format(",".join(vertices)))

    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )

file_name = "photo_2023-06-26_16-53-48.jpg"
detect_text(file_name)