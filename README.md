# autolabeler_coco_student
一种利用chatgpt4-view模型半自动标注的方式，主要用于coco格式的课堂学生目标检测数据集标注。

## 运行方式 

python coco_auto_openai_student.py 

## 需要传入的参数

    input_folder = "图片文件夹"
    output_folder = "输出标注文件夹"
    
## 提示词如下

Identify and outline the entire target of any student in the image. "
        "Provide bounding boxes that encompass the full extent of each object, "
        "ensuring that all parts, such as the face, legs, and tail, are included within. "
        "Minimize the inclusion of background space as much as possible. "
        "Return the bounding box coordinates in a JSON array named 'results', "
        "with 'label' and 'coordinates' for each object. "
        "The 'coordinates' should detail 'x1', 'y1' (top-left corner), and 'x2', 'y2' "
        "(bottom-right corner) following the PIL draw method's requirements.




感谢以下项目的启发：

https://github.com/Flode-Labs/auto-labeler
