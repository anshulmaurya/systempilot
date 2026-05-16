import Vision

from utils import image_to_nsdata


def run_vision_ocr(img):
    data = image_to_nsdata(img)

    request = Vision.VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    request.setUsesLanguageCorrection_(True)

    handler = Vision.VNImageRequestHandler.alloc().initWithData_options_(
        data,
        None,
    )

    success, error = handler.performRequests_error_([request], None)

    if error:
        print("Vision error:", error)
        return []

    results = request.results() or []

    img_width, img_height = img.size
    ocr_items = []

    for observation in results:
        candidates = observation.topCandidates_(1)

        if not candidates:
            continue

        text = candidates[0].string()
        bbox = observation.boundingBox()

        # Vision bbox: normalized coordinates, origin bottom-left
        box_x = bbox.origin.x * img_width
        box_y = (1 - bbox.origin.y - bbox.size.height) * img_height
        box_w = bbox.size.width * img_width
        box_h = bbox.size.height * img_height

        ocr_items.append({
            "text": text,
            "x": box_x,
            "y": box_y,
            "w": box_w,
            "h": box_h,
            "center_x": box_x + box_w / 2,
            "center_y": box_y + box_h / 2,
        })

    return ocr_items
