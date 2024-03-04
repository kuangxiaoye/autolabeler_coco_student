import base64
import requests
import os
from PIL import Image, ImageDraw
import json
import xml.etree.ElementTree as ET

# OpenAI API Key
api_key = "这里输入你自己的apikey"

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Function to perform object detection and labeling

def detect_objects(image_path, labels):
    label_list = ', '.join([f"'{label}'" for label in labels])
    prompt_text = (
        f"Identify and outline the entire target of any {label_list} in the image. "
        "Provide bounding boxes that encompass the full extent of each object, "
        "ensuring that all parts, such as the face, legs, and tail, are included within. "
        "Minimize the inclusion of background space as much as possible. "
        "Return the bounding box coordinates in a JSON array named 'results', "
        "with 'label' and 'coordinates' for each object. "
        "The 'coordinates' should detail 'x1', 'y1' (top-left corner), and 'x2', 'y2' "
        "(bottom-right corner) following the PIL draw method's requirements."
    )
    base64_image = encode_image(image_path)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
        {
            "role": "system",
            "content": prompt_text
        },
        {
            "role": "user",
            "content": [

            {
                "type": "image_url",
                "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
                }
            }
            ]
        }
        ],
        "max_tokens": 700
    }

    try:
        response = requests.post("https://api.baipiaoai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        res_json_bf = response.json()
        res_json = res_json_bf["choices"][0]["message"]["content"].split("```json")[1].split("```")[0]
        result = json.loads(res_json)
        
        image = Image.open(image_path)
       
        original_width, original_height= image.size
        
        
        scaled_side = 768
        if (min(original_height, original_width) > scaled_side):
            combined_scale_factor = min(original_height, original_width) / scaled_side
        else:
            combined_scale_factor = 1

        for item in result["results"]:
            coords = item["coordinates"]
            item["coordinates"]["x1"] = int(coords["x1"] * combined_scale_factor)
            item["coordinates"]["y1"] = int(coords["y1"] * combined_scale_factor)
            item["coordinates"]["x2"] = int(coords["x2"] * combined_scale_factor)
            item["coordinates"]["y2"] = int(coords["y2"] * combined_scale_factor)
        
        draw = ImageDraw.Draw(image)

        for obj in result["results"]:
            coords = obj['coordinates']
            # 绘制边框
            draw.rectangle([coords['x1'], coords['y1'], coords['x2'], coords['y2']], outline="red", width=3)

        if image.mode in ("RGBA", "LA"):
            image = image.convert("RGB")
        image.save(image_path+"_annotated.jpg")

        print(result["results"])
        return result["results"]
    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")
        return []


def process_images_in_folder(input_folder, output_format, output_folder, labels):
    image_paths = []
    detected_objects_all = []
    for filename in os.listdir(input_folder):
        if filename.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
            image_path = os.path.join(input_folder, filename)
            objects = detect_objects(image_path, labels)
            image_paths.append(image_path)
            detected_objects_all.append(objects)

    if output_format == "coco":
        save_coco_annotations(image_paths, detected_objects_all, output_folder)
    # Handle other formats (tf, json) as before


def save_coco_annotations(image_paths, detected_objects, output_folder):
    coco_output = {
        "images": [],
        "annotations": [],
        "categories": []
    }

    category_id_map = {}
    annotation_id = 1

    for image_path, objects in zip(image_paths, detected_objects):
        image = Image.open(image_path)
        image_info = {
            "id": len(coco_output["images"]) + 1,
            "file_name": os.path.basename(image_path),
            "width": image.width,
            "height": image.height
        }
        coco_output["images"].append(image_info)

        for obj in objects:
            category_name = obj["label"]
            if category_name not in category_id_map:
                category_id = len(coco_output["categories"]) + 1
                category_id_map[category_name] = category_id
                coco_output["categories"].append({
                    "id": category_id,
                    "name": category_name
                })

            x_min, y_min = obj["coordinates"]["x1"], obj["coordinates"]["y1"]
            width = obj["coordinates"]["x2"] - obj["coordinates"]["x1"]
            height = obj["coordinates"]["y2"] - obj["coordinates"]["y1"]

            annotation = {
                "id": annotation_id,
                "image_id": image_info["id"],
                "category_id": category_id_map[category_name],
                "bbox": [x_min, y_min, width, height],
                "area": width * height,
                "iscrowd": 0
            }
            coco_output["annotations"].append(annotation)
            annotation_id += 1

    with open(os.path.join(output_folder, "annotations.json"), "w") as file:
        json.dump(coco_output, file, indent=4)
  
            
# Main function 
def main():
    input_folder = "/root/autodl-tmp/auto-labeler/images"
    output_format = "coco"  # Choose "tf" or "json"
    output_folder = "./annotations"
    labels = ['student']

    try:
        os.makedirs(output_folder, exist_ok=True)
    except OSError as e:
        print(f"Error creating output directory: {e}")
        return
    process_images_in_folder(input_folder, output_format, output_folder,labels)

if __name__ == "__main__":
    main()
