import cv2
import random
import colorsys
import numpy as np
import tensorflow as tf
from core.config import cfg
import csv

def load_weights_tiny(model, weights_file):
    wf = open(weights_file, 'rb')
    major, minor, revision, seen, _ = np.fromfile(wf, dtype=np.int32, count=5)

    j = 0
    for i in range(13):
        conv_layer_name = 'conv2d_%d' % i if i > 0 else 'conv2d'
        bn_layer_name = 'batch_normalization_%d' % j if j > 0 else 'batch_normalization'

        conv_layer = model.get_layer(conv_layer_name)
        filters = conv_layer.filters
        k_size = conv_layer.kernel_size[0]
        in_dim = conv_layer.input_shape[-1]

        if i not in [9, 12]:
            # darknet weights: [beta, gamma, mean, variance]
            bn_weights = np.fromfile(wf, dtype=np.float32, count=4 * filters)
            # tf weights: [gamma, beta, mean, variance]
            bn_weights = bn_weights.reshape((4, filters))[[1, 0, 2, 3]]
            bn_layer = model.get_layer(bn_layer_name)
            j += 1
        else:
            conv_bias = np.fromfile(wf, dtype=np.float32, count=filters)

        # darknet shape (out_dim, in_dim, height, width)
        conv_shape = (filters, in_dim, k_size, k_size)
        conv_weights = np.fromfile(wf, dtype=np.float32, count=np.product(conv_shape))
        # tf shape (height, width, in_dim, out_dim)
        conv_weights = conv_weights.reshape(conv_shape).transpose([2, 3, 1, 0])

        if i not in [9, 12]:
            conv_layer.set_weights([conv_weights])
            bn_layer.set_weights(bn_weights)
        else:
            conv_layer.set_weights([conv_weights, conv_bias])

    assert len(wf.read()) == 0, 'failed to read all data'
    wf.close()

def load_weights_v3(model, weights_file):
    wf = open(weights_file, 'rb')
    major, minor, revision, seen, _ = np.fromfile(wf, dtype=np.int32, count=5)

    j = 0
    for i in range(75):
        conv_layer_name = 'conv2d_%d' % i if i > 0 else 'conv2d'
        bn_layer_name = 'batch_normalization_%d' % j if j > 0 else 'batch_normalization'

        conv_layer = model.get_layer(conv_layer_name)
        filters = conv_layer.filters
        k_size = conv_layer.kernel_size[0]
        in_dim = conv_layer.input_shape[-1]

        if i not in [58, 66, 74]:
            # darknet weights: [beta, gamma, mean, variance]
            bn_weights = np.fromfile(wf, dtype=np.float32, count=4 * filters)
            # tf weights: [gamma, beta, mean, variance]
            bn_weights = bn_weights.reshape((4, filters))[[1, 0, 2, 3]]
            bn_layer = model.get_layer(bn_layer_name)
            j += 1
        else:
            conv_bias = np.fromfile(wf, dtype=np.float32, count=filters)

        # darknet shape (out_dim, in_dim, height, width)
        conv_shape = (filters, in_dim, k_size, k_size)
        conv_weights = np.fromfile(wf, dtype=np.float32, count=np.product(conv_shape))
        # tf shape (height, width, in_dim, out_dim)
        conv_weights = conv_weights.reshape(conv_shape).transpose([2, 3, 1, 0])

        if i not in [58, 66, 74]:
            conv_layer.set_weights([conv_weights])
            bn_layer.set_weights(bn_weights)
        else:
            conv_layer.set_weights([conv_weights, conv_bias])

    assert len(wf.read()) == 0, 'failed to read all data'
    wf.close()

###---------------------------------------------------------------------------
#   Loads existing yolo weights into tf model

def load_weights(model, weights_file):
    wf = open(weights_file, 'rb')
    major, minor, revision, seen, _ = np.fromfile(wf, dtype=np.int32, count=5)

    j = 0
    for i in range(110):
        conv_layer_name = 'conv2d_%d' %i if i > 0 else 'conv2d'
        bn_layer_name = 'batch_normalization_%d' %j if j > 0 else 'batch_normalization'


        conv_layer = model.get_layer(conv_layer_name)
        filters = conv_layer.filters
        k_size = conv_layer.kernel_size[0]
        in_dim = conv_layer.input_shape[-1]

        if i not in [93, 101, 109]:
            # darknet weights: [beta, gamma, mean, variance]
            bn_weights = np.fromfile(wf, dtype=np.float32, count=4 * filters)
            # tf weights: [gamma, beta, mean, variance]
            bn_weights = bn_weights.reshape((4, filters))[[1, 0, 2, 3]]
            bn_layer = model.get_layer(bn_layer_name)
            j += 1
        else:
            conv_bias = np.fromfile(wf, dtype=np.float32, count=filters)

        # darknet shape (out_dim, in_dim, height, width)
        conv_shape = (filters, in_dim, k_size, k_size)
        conv_weights = np.fromfile(wf, dtype=np.float32, count=np.product(conv_shape))
        # tf shape (height, width, in_dim, out_dim)
        conv_weights = conv_weights.reshape(conv_shape).transpose([2, 3, 1, 0])

        if i not in [93, 101, 109]:
            conv_layer.set_weights([conv_weights])
            bn_layer.set_weights(bn_weights)
        else:
            conv_layer.set_weights([conv_weights, conv_bias])

    assert len(wf.read()) == 0, 'failed to read all data'
    wf.close()

 
def read_class_names(class_file_name):
    '''loads class name from a file'''
    names = {}
    with open(class_file_name, 'r') as data:
        for ID, name in enumerate(data):
            names[ID] = name.strip('\n')
    return names


def get_anchors(anchors_path, tiny=False):
    '''loads the anchors from a file'''
    with open(anchors_path) as f:
        anchors = f.readline()
    anchors = np.array(anchors.split(','), dtype=np.float32)
    if tiny:
        return anchors.reshape(2, 3, 2)
    else:
        return anchors.reshape(3, 3, 2)

###---------------------------------------------------------------------------
#   Scales photos to input size

def image_preprocess(image, target_size, gt_boxes=None):

    ih, iw    = target_size
    h,  w, _  = image.shape

    scale = min(iw/w, ih/h)
    nw, nh  = int(scale * w), int(scale * h)
    image_resized = cv2.resize(image, (nw, nh))

    image_paded = np.full(shape=[ih, iw, 3], fill_value=128.0)
    dw, dh = (iw - nw) // 2, (ih-nh) // 2
    image_paded[dh:nh+dh, dw:nw+dw, :] = image_resized
    image_paded = image_paded / 255.

    if gt_boxes is None:
        return image_paded

    else:
        gt_boxes[:, [0, 2]] = gt_boxes[:, [0, 2]] * scale + dw
        gt_boxes[:, [1, 3]] = gt_boxes[:, [1, 3]] * scale + dh
        return image_paded, gt_boxes

###---------------------------------------------------------------------------
#   Given bbox info, draws rectangle around object
 
def draw_bbox(image, bboxes, classes=read_class_names(cfg.YOLO.CLASSES), show_label=True):
    """
    bboxes: [x_min, y_min, x_max, y_max, probability, cls_id] format coordinates.
    """

    num_classes = len(classes)
    image_h, image_w, _ = image.shape
    # hsv_tuples = [(1.0 * x / num_classes, 1., 1.) for x in range(num_classes)]
    # colors = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))
    # colors = list(map(lambda x: (int(x[0] * 255), int(x[1] * 255), int(x[2] * 255)), colors))

    random.seed(0)
    # random.shuffle(colors)
    random.seed(None)

    for i, bbox in enumerate(bboxes):
        coor = np.array(bbox[:4], dtype=np.int32)
        fontScale = 0.5
        score = bbox[4]
        class_ind = int(bbox[5])
        # bbox_color = colors[class_ind]
        bbox_color = (0,0,0)
        bbox_thick = int(0.6 * (image_h + image_w) / 600)
        image = find_blur_face(coor, image)
        c1, c2 = (coor[0], coor[1]), (coor[2], coor[3])
        cv2.rectangle(image, c1, c2, bbox_color, bbox_thick)

        if show_label:
            bbox_mess = '%s: %.2f' % (classes[class_ind], score)
            t_size = cv2.getTextSize(bbox_mess, 0, fontScale, thickness=bbox_thick//2)[0]
            cv2.rectangle(image, c1, (c1[0] + t_size[0], c1[1] - t_size[1] - 3), bbox_color, -1)  # filled

            cv2.putText(image, bbox_mess, (c1[0], c1[1]-2), cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale, (0, 0, 0), bbox_thick//2, lineType=cv2.LINE_AA)

    return image

def find_blur_face(coor, image):
    x_min = coor[0]
    y_min = coor[1]
    x_max = coor[2]
    y_max = y_min + (coor[3] - coor[1])//3
    
    face = image[y_min:y_max, x_min:x_max]
    
    blurred_face = anonymize_face_pixelate(face, blocks=6)
    
    image[y_min:y_max, x_min:x_max] = blurred_face
    return image
    
    
#from https://www.pyimagesearch.com/2020/04/06/blur-and-anonymize-faces-with-opencv-and-python/
def anonymize_face_simple(image, factor=3.0):
	# automatically determine the size of the blurring kernel based
	# on the spatial dimensions of the input image
	(h, w) = image.shape[:2]
	kW = int(w / factor)
	kH = int(h / factor)
	# ensure the width of the kernel is odd
	if kW % 2 == 0:
		kW -= 1
	# ensure the height of the kernel is odd
	if kH % 2 == 0:
		kH -= 1
	# apply a Gaussian blur to the input image using our computed
	# kernel size
	return cv2.GaussianBlur(image, (kW, kH), 0)
#from https://www.pyimagesearch.com/2020/04/06/blur-and-anonymize-faces-with-opencv-and-python/

def anonymize_face_pixelate(image, blocks=3):
	# divide the input image into NxN blocks
	(h, w) = image.shape[:2]
	xSteps = np.linspace(0, w, blocks + 1, dtype="int")
	ySteps = np.linspace(0, h, blocks + 1, dtype="int")
	# loop over the blocks in both the x and y direction
	for i in range(1, len(ySteps)):
		for j in range(1, len(xSteps)):
			# compute the starting and ending (x, y)-coordinates
			# for the current block
			startX = xSteps[j - 1]
			startY = ySteps[i - 1]
			endX = xSteps[j]
			endY = ySteps[i]
			# extract the ROI using NumPy array slicing, compute the
			# mean of the ROI, and then draw a rectangle with the
			# mean RGB values over the ROI in the original image
			roi = image[startY:endY, startX:endX]
			(B, G, R) = [int(x) for x in cv2.mean(roi)[:3]]
			cv2.rectangle(image, (startX, startY), (endX, endY),
				(B, G, R), -1)
	# return the pixelated blurred image
	return image

def bboxes_iou(boxes1, boxes2):

    boxes1 = np.array(boxes1)
    boxes2 = np.array(boxes2)

    boxes1_area = (boxes1[..., 2] - boxes1[..., 0]) * (boxes1[..., 3] - boxes1[..., 1])
    boxes2_area = (boxes2[..., 2] - boxes2[..., 0]) * (boxes2[..., 3] - boxes2[..., 1])

    left_up       = np.maximum(boxes1[..., :2], boxes2[..., :2])
    right_down    = np.minimum(boxes1[..., 2:], boxes2[..., 2:])

    inter_section = np.maximum(right_down - left_up, 0.0)
    inter_area    = inter_section[..., 0] * inter_section[..., 1]
    union_area    = boxes1_area + boxes2_area - inter_area
    ious          = np.maximum(1.0 * inter_area / union_area, np.finfo(np.float32).eps)

    return ious

def bboxes_ciou(boxes1, boxes2):

    boxes1 = np.array(boxes1)
    boxes2 = np.array(boxes2)

    left = np.maximum(boxes1[..., 0], boxes2[..., 0])
    up = np.maximum(boxes1[..., 1], boxes2[..., 1])
    right = np.maximum(boxes1[..., 2], boxes2[..., 2])
    down = np.maximum(boxes1[..., 3], boxes2[..., 3])

    c = (right - left) * (right - left) + (up - down) * (up - down)
    iou = bboxes_iou(boxes1, boxes2)

    ax = (boxes1[..., 0] + boxes1[..., 2]) / 2
    ay = (boxes1[..., 1] + boxes1[..., 3]) / 2
    bx = (boxes2[..., 0] + boxes2[..., 2]) / 2
    by = (boxes2[..., 1] + boxes2[..., 3]) / 2

    u = (ax - bx) * (ax - bx) + (ay - by) * (ay - by)
    d = u/c

    aw = boxes1[..., 2] - boxes1[..., 0]
    ah = boxes1[..., 3] - boxes1[..., 1]
    bw = boxes2[..., 2] - boxes2[..., 0]
    bh = boxes2[..., 3] - boxes2[..., 1]

    ar_gt = bw/bh
    ar_pred = aw/ah

    ar_loss = 4 / (np.pi * np.pi) * (np.arctan(ar_gt) - np.arctan(ar_pred)) * (np.arctan(ar_gt) - np.arctan(ar_pred))
    alpha = ar_loss / (1 - iou + ar_loss + 0.000001)
    ciou_term = d + alpha * ar_loss

    return iou - ciou_term

###---------------------------------------------------------------------------
#   Filters out excessively overlapping bboxes (I think)
   
def nms(bboxes, iou_threshold, sigma=0.3, method='nms'):
    """
    :param bboxes: (xmin, ymin, xmax, ymax, score, class)

    Note: soft-nms, https://arxiv.org/pdf/1704.04503.pdf
          https://github.com/bharatsingh430/soft-nms
    """
    classes_in_img = list(set(bboxes[:, 5]))
    best_bboxes = []

    for cls in classes_in_img:
        cls_mask = (bboxes[:, 5] == cls)
        cls_bboxes = bboxes[cls_mask]

        while len(cls_bboxes) > 0:
            max_ind = np.argmax(cls_bboxes[:, 4])
            best_bbox = cls_bboxes[max_ind]
            best_bboxes.append(best_bbox)
            cls_bboxes = np.concatenate([cls_bboxes[: max_ind], cls_bboxes[max_ind + 1:]])
            iou = bboxes_iou(best_bbox[np.newaxis, :4], cls_bboxes[:, :4])
            weight = np.ones((len(iou),), dtype=np.float32)

            assert method in ['nms', 'soft-nms']

            if method == 'nms':
                iou_mask = iou > iou_threshold
                weight[iou_mask] = 0.0

            if method == 'soft-nms':
                weight = np.exp(-(1.0 * iou ** 2 / sigma))

            cls_bboxes[:, 4] = cls_bboxes[:, 4] * weight
            score_mask = cls_bboxes[:, 4] > 0.
            cls_bboxes = cls_bboxes[score_mask]

    return best_bboxes

def diounms_sort(bboxes, iou_threshold, sigma=0.3, method='nms', beta_nms=0.6):
    best_bboxes = []
    return best_bboxes

def postprocess_bbbox(pred_bbox, ANCHORS, STRIDES, XYSCALE=[1,1,1]):
    # print(len(pred_bbox))

    for i, pred in enumerate(pred_bbox):
        # print(pred.shape)
        conv_shape = pred.shape
        output_size = conv_shape[1]
        conv_raw_dxdy = pred[:, :, :, :, 0:2]
        conv_raw_dwdh = pred[:, :, :, :, 2:4]
        xy_grid = np.meshgrid(np.arange(output_size), np.arange(output_size))
        xy_grid = np.expand_dims(np.stack(xy_grid, axis=-1), axis=2)  # [gx, gy, 1, 2]

        xy_grid = np.tile(tf.expand_dims(xy_grid, axis=0), [1, 1, 1, 3, 1])
        xy_grid = xy_grid.astype(np.float)

        # print(xy_grid.shape)
        # pred_xy = (tf.sigmoid(conv_raw_dxdy) + xy_grid) * STRIDES[i]
        pred_xy = ((tf.sigmoid(conv_raw_dxdy) * XYSCALE[i]) - 0.5 * (XYSCALE[i] - 1) + xy_grid) * STRIDES[i]
        # pred_wh = (tf.exp(conv_raw_dwdh) * ANCHORS[i]) * STRIDES[i]
        pred_wh = (tf.exp(conv_raw_dwdh) * ANCHORS[i])
        pred[:, :, :, :, 0:4] = tf.concat([pred_xy, pred_wh], axis=-1)
        # print(pred.shape)

    pred_bbox = [tf.reshape(x, (-1, tf.shape(x)[-1])) for x in pred_bbox]
    # print(np.array(pred_bbox).shape)
    pred_bbox = tf.concat(pred_bbox, axis=0)
    # print(np.array(pred_bbox).shape)
    return pred_bbox

###---------------------------------------------------------------------------
#   Filters out bboxes that are not within the image, are not scaled properly, or are invalid
#   Returns remaining bboxes
   
def postprocess_boxes(pred_bbox, org_img_shape, input_size, score_threshold):
    

    valid_scale=[0, np.inf]
    
    #append batch # to end
    
    # size = pred_bbox.shape[0]
    # a = np.array([[0]] * size)
    # print(a.shape)
    #convert to numpy array
    pred_bbox = np.array(pred_bbox)
    # pred_bbox = np.append(pred_bbox, a, axis = 1)
    # print(pred_bbox.shape)
    # pred_bbox[10648:, -1] = 1
    # print(pred_bbox.shape)
    

    #separate out box dimensions nd and probability
    pred_xywh = pred_bbox[:, 0:4]
    pred_conf = pred_bbox[:, 4]
    pred_prob = pred_bbox[:, 5:]
    
    # image_nums = pred_bbox[:, -1]
    
    #find corners of bboxes and scale properly
    # # (1) (x, y, w, h) --> (xmin, ymin, xmax, ymax)
    pred_coor = np.concatenate([pred_xywh[:, :2] - pred_xywh[:, 2:] * 0.5,
                                pred_xywh[:, :2] + pred_xywh[:, 2:] * 0.5], axis=-1)
    # # (2) (xmin, ymin, xmax, ymax) -> (xmin_org, ymin_org, xmax_org, ymax_org)
    org_h, org_w = org_img_shape
    resize_ratio = min(input_size / org_w, input_size / org_h)

    dw = (input_size - resize_ratio * org_w) / 2
    dh = (input_size - resize_ratio * org_h) / 2

    pred_coor[:, 0::2] = 1.0 * (pred_coor[:, 0::2] - dw) / resize_ratio
    pred_coor[:, 1::2] = 1.0 * (pred_coor[:, 1::2] - dh) / resize_ratio

    # # (3) clip some boxes those are out of range
    pred_coor = np.concatenate([np.maximum(pred_coor[:, :2], [0, 0]),
                                np.minimum(pred_coor[:, 2:], [org_w - 1, org_h - 1])], axis=-1)
    #mask out coordinates that are not in viewable space
    invalid_mask = np.logical_or((pred_coor[:, 0] > pred_coor[:, 2]), (pred_coor[:, 1] > pred_coor[:, 3]))
    pred_coor[invalid_mask] = 0

    # # (4) discard some invalid boxes
    # ensures bbox scale is positive
    bboxes_scale = np.sqrt(np.multiply.reduce(pred_coor[:, 2:4] - pred_coor[:, 0:2], axis=-1))
    scale_mask = np.logical_and((valid_scale[0] < bboxes_scale), (bboxes_scale < valid_scale[1]))

    # # (5) discard some boxes with low scores
    classes = np.argmax(pred_prob, axis=-1)
    scores = pred_conf * pred_prob[np.arange(len(pred_coor)), classes]
    # scores = pred_prob[np.arange(len(pred_coor)), classes]
    score_mask = scores > score_threshold
    mask = np.logical_and(scale_mask, score_mask)
    
    #qualities of bounding boxm - trims out all bboxes that aren't within screen, properly scaled, too low of a score
    coors, scores, probs, classes = pred_coor[mask], scores[mask], pred_prob[mask], classes[mask] #, image_nums[mask]
    bboxes = np.concatenate([coors, scores[:, np.newaxis], classes[:, np.newaxis]], axis=-1)
    
    return bboxes, probs, classes #, image_nums


###---------------------------------------------------------------------------
#   Filters out all but people and returns their bboxes

def filter_people(bboxes, probs, classes):#, image_num):
    #list of bboxes that mark a person
    people_bboxes = []
    # people_bboxes2 = []

    # takes objects primarily identified as a person and filters out ones with relatively high chances
    # of being non-human
    for i, prob in enumerate(probs): 
        if classes[i] == 0:
            #commonly mistaken objects
            light = prob[9]
            fire = prob[10]
            stop = prob[11]
            parking = prob[12]
            bench = prob[13]
            #print(prob[9:14])
            if (light < 0.002 and fire < 0.002 and stop < 0.002 and parking < 0.002 and bench < 0.002): 
                people_bboxes.append(bboxes[i])
                # if image_num[i] == 0:
                #     people_bboxes.append(bboxes[i])
                # elif image_num[i] ==1:
                #     people_bboxes2.append(bboxes[i])

    people_bboxes = np.array(people_bboxes)
    # people_bboxes2 = np.array(people_bboxes2)

    return people_bboxes #, people_bboxes2


def freeze_all(model, frozen=True):
    model.trainable = not frozen
    if isinstance(model, tf.keras.Model):
        for l in model.layers:
            freeze_all(l, frozen)
def unfreeze_all(model, frozen=False):
    model.trainable = not frozen
    if isinstance(model, tf.keras.Model):
        for l in model.layers:
            unfreeze_all(l, frozen)
            

###---------------------------------------------------------------------------
#   Outputs oocupancy data to a txt file

def video_write_info(f, real_ftpts, dt, count, people, avg_dist, avg_min_dist):
    pts = real_ftpts.tolist()
    f.writerow([dt, people, count, avg_dist, avg_min_dist, pts])
    

###---------------------------------------------------------------------------
#   Displays occupancy and compliance data in top right corner of video
        
def overlay_occupancy(img, count, people, size):
    
    occupants = 'Occupants : ' + str(people) + '  '
    
    #compliance is 100 if no people are present
    if people > 0:
        comp = (1 - (count / people)) * 100
    else:
        comp = 100
    compliance = '%s: %.2f %s' % ('Compliance', comp, '%')

    #calculate size text will occupy, then adjust so overlay appears in top right corner
    x = size[1]
    box = cv2.getTextSize(occupants + compliance, cv2.FONT_HERSHEY_DUPLEX, 2, 3)
    offsetx = x//30 + box[0][0]
    cv2.putText(img, occupants + compliance, ((x - offsetx), (x//30)) , cv2.FONT_HERSHEY_DUPLEX, 2, (0,0,0), 3)


###---------------------------------------------------------------------------
#   Returns point centered at bottom of bbox
        
def get_ftpts(bboxes):
    
    footpts = []
    
    #get ftpts for each bbox
    for i, bbox in enumerate(bboxes):
        
        #corner points of box
        coor = np.array(bbox[:4], dtype=np.int32)
        c1, c2 = (coor[0], coor[1]), (coor[2], coor[3])

        #add points at base of feet to list
        x = c1[0] + (c2[0] - c1[0]) // 2
        y = c2[1]
        pt = (x, y)
    
        footpts.append(pt) 
    
    #convert central foot points to numpy array            
    footpts = np.array([footpts])
    footpts = np.squeeze(np.asarray(footpts))
    
    return footpts

        
# #@tf.function    
# def draw_some_bbox(image, bboxes, classes=read_class_names(cfg.YOLO.CLASSES), show_label=False):
#     """
#     bboxes: [x_min, y_min, x_max, y_max, probability, cls_id] format coordinates.
#     """

#     num_classes = len(classes)
#     image_h, image_w, _ = image.shape
#     hsv_tuples = [(1.0 * x / num_classes, 1., 1.) for x in range(num_classes)]
#     colors = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))
#     colors = list(map(lambda x: (int(x[0] * 255), int(x[1] * 255), int(x[2] * 255)), colors))

#     random.seed(0)
#     random.shuffle(colors)
#     random.seed(None)

#     footpts = []
#     for i, bbox in enumerate(bboxes):
#         class_ind = int(bbox[5])
#         coor = np.array(bbox[:4], dtype=np.int32)
#         fontScale = 0.5
#         score = bbox[4]
#         bbox_color = colors[class_ind]
#         bbox_thick = int(0.6 * (image_h + image_w) / 600)
#         c1, c2 = (coor[0], coor[1]), (coor[2], coor[3])
#         cv2.rectangle(image, c1, c2, bbox_color, bbox_thick)
        
#         #add points at base of feet to list
#         x = c1[0] + (c2[0] - c1[0]) // 2
#         y = c2[1]
#         pt = (x, y)
    
#         footpts.append(pt)
        
    
#         if show_label:
#             bbox_mess = '%s: %.2f' % (classes[class_ind], score)
#             t_size = cv2.getTextSize(bbox_mess, 0, fontScale, thickness=bbox_thick//2)[0]
#             cv2.rectangle(image, c1, (c1[0] + t_size[0], c1[1] - t_size[1] - 3), bbox_color, -1)  # filled
    
#             cv2.putText(image, bbox_mess, (c1[0], c1[1]-2), cv2.FONT_HERSHEY_SIMPLEX,
#                         fontScale, (0, 0, 0), bbox_thick//2, lineType=cv2.LINE_AA)
    
#     #convert central foot points to numpy array            
#     footpts = np.array([footpts])
#     footpts = np.squeeze(np.asarray(footpts))
    
#     return image, footpts

# def write_bbox_info(image, path, bboxes, classes=read_class_names(cfg.YOLO.CLASSES)):
#     output_f = path[:-3] + 'txt'
#     f = open(output_f, 'w')
    
#     ped = 0
#     vehicle = 0
#     bike = 0
#     for i, bbox in enumerate(bboxes):
#         class_ind = int(bbox[5])
#         if classes[class_ind] == 'person':
#             ped = ped + 1    
#         elif classes[class_ind] == 'bicycle':
#             bike = bike + 1
#         elif classes[class_ind] == 'motorbike' or classes[class_ind] == 'car' or classes[class_ind] == 'truck' or classes[class_ind] == 'bus':
#             vehicle = vehicle + 1
    
#     # write image name + timestamp f.write()
#     f.write('Pedestrians: ' + str(ped))
#     f.write('   Vehicles: ' + str(vehicle))
#     f.write('   Bike: ' + str(bike))
#     f.close()
    
#FIXME can get rid of above code by simple rewrite in detect.py
            
  # def count_people(bboxes, classes=read_class_names(cfg.YOLO.CLASSES)):
  #   ped = 0
  #   for i, bbox in enumerate(bboxes):
  #       class_ind = int(bbox[5])
  #       if classes[class_ind] == 'person':
  #           ped = ped + 1 
            
  #   return ped 

    
