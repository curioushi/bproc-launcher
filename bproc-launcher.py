import os
import os.path as osp
import sys
import subprocess
import argparse
from random import choice
from loguru import logger
from omegaconf import OmegaConf
from config_setup_app import ConfigSetupApp


logger.remove()
logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green>| <level>{message}</level>")

RUN_ID = ''.join([choice('0123456789abcdef') for _ in range(8)])
HOME = '/home/bproc'
IMAGE_NAME = 'curioushi/bproc:latest'

def run_bproc_docker(model_path, output_dir, cfg, textures_dir=None, gpu_id='0', interactive=False):
    logger.info('-' * 80)
    logger.info(f'RUN_ID = {RUN_ID}')
    logger.info(f'Docker image: {IMAGE_NAME}')
    logger.info(f'All Config: {cfg}')

    model_name = osp.basename(model_path)
    tmp_config_path = f'/tmp/config_{RUN_ID}.yaml'
    with open(tmp_config_path, 'w') as f:
        OmegaConf.save(config=cfg, f=f.name)

    args = ['docker', 'run', '-it', '--rm']
    args += ['--gpus', f'\"device={gpu_id}\"']
    args += ['--name', f'bproc_{RUN_ID}']
    args += ['--volume=/dev/shm:/dev/shm:rw']

    args += [f'--volume={model_path}:{HOME}/input/{model_name}:ro']
    args += [f'--volume={tmp_config_path}:{HOME}/config.yaml:rw']
    if textures_dir:
        args += [f'--volume={textures_dir}:{HOME}/input/cc_textures:ro']
    args += [f'--volume={output_dir}:{HOME}/output:rw']

    args += [IMAGE_NAME]

    if interactive:
        args += ['/bin/bash']
    else:
        args += ['/bin/bash', '-c', './BlenderProc/run.sh config.yaml']

    code = subprocess.Popen(args).wait()

def pull_docker_image():
    logger.info(f'Pull latest docker image')
    args = ['docker', 'pull', IMAGE_NAME]
    code = subprocess.Popen(args).wait()

def setup_config(config_path, model_path, tui=False):
    # modify the model file path
    cfg = OmegaConf.load(config_path)
    cfg.OBJECT.FILE = f'{HOME}/input/{osp.basename(model_path)}'

    if tui:
        app = ConfigSetupApp(config=cfg)
        cfg = app.run()

    return cfg

def parse_args():
    def norm_abs_path(filepath):
        return osp.normpath(osp.abspath(filepath))
    parser = argparse.ArgumentParser()
    parser.add_argument('model_path', type=str, help='Path to object model, supported format: obj, stl, ply')
    parser.add_argument('output_dir', type=str, help='Output directory')
    parser.add_argument('-c', '--config', type=str, default='path/to/config.yaml', help='YAML configuration file, used to configure the synthetic options.')
    parser.add_argument('-t', '--textures_dir', type=str, default='path/to/cc_textures',
                        help='CC0 textures directory. Set this value to enable material randomization.')
    parser.add_argument('-g', '--gpu', type=str, default='0', help='GPU ID, e.g. 0 will use the first gpu. (default=0)')
    parser.add_argument('-it', '--it', action='store_true', help='Enter into container with interactive mode.')
    parser.add_argument('-tui', '--tui', action='store_true', help='Edit the YAML configuration with TUI.')
    args = parser.parse_args()

    args.model_path = norm_abs_path(args.model_path)
    assert os.path.exists(args.model_path)

    args.output_dir = norm_abs_path(args.output_dir)
    os.makedirs(args.output_dir, exist_ok=True)

    args.textures_dir = norm_abs_path(args.textures_dir)
    if not os.path.exists(args.textures_dir):
        logger.warning('testures_dir does not exist. Material randomization is disabled.')
        args.textures_dir=None

    args.config = norm_abs_path(args.config)
    if not os.path.exists(args.config):
        logger.warning('config file not found, use the default configuration.')
        args.config = norm_abs_path(osp.join(osp.dirname(__file__), 'config.yaml'))
        if not os.path.exists(args.config): # still not found
            logger.error('default configuration file not found.')
            sys.exit(-1)

    logger.info('-' * 35 + ' Arguments ' + '-' * 34)
    for name, value in vars(args).items():
        logger.info(f'{name} = {value}')
    return args

if __name__ == '__main__':
    args = parse_args()
    cfg = setup_config(args.config, args.model_path, tui=args.tui)
    pull_docker_image()
    run_bproc_docker(
            args.model_path,
            args.output_dir,
            cfg,
            interactive=args.it,
            textures_dir=args.textures_dir,
            gpu_id=args.gpu)


