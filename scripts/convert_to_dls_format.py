import os
import sys
import os.path as osp
from glob import glob
from loguru import logger
from shapely.geometry import Polygon
from tqdm import tqdm
from random import choice
import numpy as np
import cv2
import json
import shutil
import argparse


def read_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)


def write_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir')
    parser.add_argument('output_dir')
    parser.add_argument('-v', '--visib_frac', type=float, default=0.5)
    parser.add_argument('--train_frac', type=int, default=70)
    parser.add_argument('--test_frac', type=int, default=15)
    parser.add_argument('--val_frac', type=int, default=15)
    args = parser.parse_args()
    if not osp.exists(args.input_dir):
        logger.error('input directory not found: {}'.format(args.input_dir))
        sys.exit(-1)
    shutil.rmtree(args.output_dir, ignore_errors=True)
    os.makedirs(args.output_dir, exist_ok=True)
    return args


def random_split(train_frac, val_frac, test_frac):
    r = np.random.random() * (train_frac + val_frac + test_frac)
    if r < train_frac:
        return 'train'
    elif r < train_frac + val_frac:
        return 'val'
    else:
        return 'test'


def convert_bproc_to_dls(args):
    input_dir = args.input_dir
    output_dir = args.output_dir

    output_data_dir = osp.join(output_dir, 'data')
    output_anno_dir = osp.join(output_dir, 'annotation_test')
    os.makedirs(output_data_dir, exist_ok=True)
    os.makedirs(output_anno_dir, exist_ok=True)

    scene_dirs = [x for x in sorted(
        glob(osp.join(input_dir, '*'))) if osp.isdir(x)]

    global_index = 0
    width = None
    height = None
    samples_fp = open(osp.join(output_dir, 'samples_v2.txt'), 'w')
    for scene_dir in scene_dirs:
        color_dir = osp.join(scene_dir, 'color')
        mask_visib_dir = osp.join(scene_dir, 'mask_visib')
        annotations_json = osp.join(scene_dir, 'annotations.json')
        assert osp.exists(color_dir)
        assert osp.exists(mask_visib_dir)
        assert osp.exists(annotations_json)
        annos = read_json(annotations_json)
        for image_id, anno in tqdm(annos.items()):
            input_img_path = osp.join(color_dir, f'{image_id}.png')
            output_img_path = osp.join(
                output_data_dir, f'{global_index:08}.png')
            shutil.copy(input_img_path, output_img_path)
            if width is None or height is None:
                height, width = cv2.imread(input_img_path).shape[:2]

            anno_out = dict()
            anno_out['width'] = width
            anno_out['height'] = height
            anno_out['path'] = osp.join('data', f'{global_index:08}.png')
            anno_out['image_category'] = ""
            anno_out['segments'] = []
            anno_out['instances'] = []

            x1_out, y1_out, x2_out, y2_out = [], [], [], []
            for inst_id, inst in enumerate(anno):
                visib_frac = inst['visib_frac']
                if visib_frac < args.visib_frac:
                    continue

                x, y, w, h = inst['bbox_visib']
                x1, y1, x2, y2 = x, y, x + w, y + h
                x1_out.append(x1)
                y1_out.append(y1)
                x2_out.append(x2)
                y2_out.append(y2)

                segmentation = []
                mask_path = osp.join(
                    mask_visib_dir, f'{image_id}_{inst_id:06}.png')
                assert osp.exists(mask_path)
                mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
                contours, _ = cv2.findContours(
                    mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
                for c in contours:
                    c = c.reshape(-1, 2)
                    if c.shape[0] < 4:
                        continue
                    poly = Polygon(c)
                    poly_s = poly.simplify(0.1)
                    segmentation.append(
                        np.array(poly_s.boundary.coords[:]).tolist())

                instance_out = dict(
                    instance_category="object",
                    isoccluded=0,
                    bbox=[x, y, w, h],
                    area=inst['px_count_visib'],
                    pose={},
                    # HACK
                    # segmentation=segmentation,
                    segmentation=[],
                    parts=[]
                )
                anno_out['instances'].append(instance_out)

            anno_out['roi'] = [
                [min(x1_out), min(y1_out)],
                [max(x2_out), min(y1_out)],
                [max(x2_out), max(y2_out)],
                [min(x1_out), max(y2_out)],
            ]
            write_json(osp.join(output_anno_dir,
                       f'{global_index:08}.json'), anno_out)
            split = random_split(
                args.train_frac, args.val_frac, args.test_frac)
            samples_fp.write(
                f'{split},annotation_test/{global_index:08}.json\n')

            global_index += 1
    samples_fp.close()

    meta = dict(
        name='synthetic-' +
        ''.join([choice('0123456789abcdef') for _ in range(8)]),
        id=int(''.join([choice('0123456789') for _ in range(8)])),
        description='',
        version=1.0,
        date_created='',
        date_modified='',
        instance_categories=['object'],
        image_categories=[],
        segment_categories=[],
        rgb='uint8',
        depth='',
        sample_num=global_index,
        entity_parts=[],
        none_entity_parts=[]
    )

    write_json(osp.join(output_dir, 'meta.json'), meta)


if __name__ == '__main__':
    args = parse_args()
    convert_bproc_to_dls(args)
