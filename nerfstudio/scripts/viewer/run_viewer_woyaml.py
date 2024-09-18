"""
主要修改點：
1.load_config 現在是 Optional[Path]：
    如果沒有提供 YAML 檔案，它會使用一個內建的預設設定，而不是報錯。
2.main 方法中增加判斷：
    在 main 中增加了 if self.load_config 的判斷來處理沒有提供 YAML 檔案的情況。
    當使用者沒有提供 YAML 時，會創建預設的 TrainerConfig 和 Pipeline，然後啟動 viewer。
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field, fields
from pathlib import Path
from threading import Lock
from typing import Literal, Optional

import tyro

# add by JiChen
from nerfstudio.viewer.preprocess_viewer import PreprocessViewer  # 從另一個腳本導入PreprocessViewer類
from nerfstudio.configs.method_configs import method_configs

from nerfstudio.configs.base_config import ViewerConfig
from nerfstudio.engine.trainer import TrainerConfig
from nerfstudio.pipelines.base_pipeline import Pipeline
from nerfstudio.utils import writer
from nerfstudio.utils.eval_utils import eval_setup
from nerfstudio.viewer.viewer import Viewer as ViewerState
from nerfstudio.viewer_legacy.server.viewer_state import ViewerLegacyState
from nerfstudio.viewer.preprocess_viewer import PreprocessViewer


@dataclass
class ViewerConfigWithoutNumRays(ViewerConfig):
    """Configuration for viewer instantiation"""

    num_rays_per_chunk: tyro.conf.Suppress[int] = -1

    def as_viewer_config(self):
        """Converts the instance to ViewerConfig"""
        return ViewerConfig(**{x.name: getattr(self, x.name) for x in fields(self)})


@dataclass
class RunViewer:
    """Load a checkpoint and start the viewer."""

    load_config: Optional[Path] = None
    """Path to config YAML file, optional."""
    viewer: ViewerConfigWithoutNumRays = field(default_factory=ViewerConfigWithoutNumRays)
    """Viewer configuration"""
    vis: Literal["viewer", "viewer_legacy"] = "viewer"
    """Type of viewer"""

    def main(self) -> None:
        """Main function."""
        if self.load_config:
            # Load configuration from YAML file if provided
            config, pipeline, _, step = eval_setup(
                self.load_config,
                eval_num_rays_per_chunk=None,
                test_mode="test",
            )
            num_rays_per_chunk = config.viewer.num_rays_per_chunk
            assert self.viewer.num_rays_per_chunk == -1
            config.vis = self.vis
            config.viewer = self.viewer.as_viewer_config()
            config.viewer.num_rays_per_chunk = num_rays_per_chunk
        else:
            # Use default configuration if no YAML file is provided
            config = method_configs["splatfacto"] # Create default TrainerConfig, method_configs["splatfacto"]
            pipeline = Pipeline()  # Create a default Pipeline instance (requires real defaults)
            step = 0  # Start from step 0 or any appropriate default step
            config.vis = self.vis
            config.viewer = self.viewer.as_viewer_config()

        _start_viewer(config, pipeline, step)

    def save_checkpoint(self, *args, **kwargs):
        """
        Mock method because we pass this instance to viewer_state.update_scene
        """


def _start_viewer(config: TrainerConfig, pipeline: Pipeline, step: int):
    """Starts the viewer

    Args:
        config: Configuration of pipeline to load
        pipeline: Pipeline instance of which to load weights
        step: Step at which the pipeline was saved
    """

    ## Add default splatfacto
    if not config.method_name:
        config.method_name = "splatfacto"

    # 如果取不到 datamanager 的 datapath，設置為空字符串
    datapath = Path()
    if hasattr(pipeline, 'datamanager') and hasattr(pipeline.datamanager, 'get_datapath'):
        datapath = pipeline.datamanager.get_datapath()

    base_dir = config.get_base_dir()
    print(f"Base Directory: {base_dir}")

    viewer_log_path = base_dir / config.viewer.relative_log_filename
    print(f"View Log Path: {base_dir}")
    
    banner_messages = None
    viewer_state = None
    viewer_callback_lock = Lock()
    if config.vis == "viewer_legacy":
        viewer_state = ViewerLegacyState(
            config.viewer,
            log_filename=viewer_log_path,
            datapath=datapath,
            pipeline=pipeline,
            train_lock=viewer_callback_lock,
        )
        banner_messages = [f"Legacy viewer at: {viewer_state.viewer_url}"]
    if config.vis == "viewer":
        viewer_state = ViewerState(
            config.viewer,
            log_filename=viewer_log_path,
            datapath=datapath,
            pipeline=pipeline,
            share=config.viewer.make_share_url,
            train_lock=viewer_callback_lock,
        )
        banner_messages = viewer_state.viewer_info

    # We don't need logging, but writer.GLOBAL_BUFFER needs to be populated
    config.logging.local_writer.enable = False
    writer.setup_local_writer(config.logging, max_iter=config.max_num_iterations, banner_messages=banner_messages)

    assert viewer_state and pipeline.datamanager.train_dataset
    viewer_state.init_scene(
        train_dataset=pipeline.datamanager.train_dataset,
        train_state="completed",
        eval_dataset=pipeline.datamanager.eval_dataset,
    )
    if isinstance(viewer_state, ViewerLegacyState):
        viewer_state.viser_server.set_training_state("completed")
    viewer_state.update_scene(step=step)
    while True:
        time.sleep(0.01)


def entrypoint():
    #"""Entrypoint for use with pyproject scripts."""
    #tyro.extras.set_accent_color("bright_yellow")
    #tyro.cli(tyro.conf.FlagConversionOff[RunViewer]).main()

    print("\033[93mViewer without YAML started\033[0m")
    # 創建 PreprocessViewer 的實例
    viewer = PreprocessViewer()
    # 啟動視覺化
    viewer.run()




if __name__ == "__main__":
    entrypoint()

# For sphinx docs
get_parser_fn = lambda: tyro.extras.get_parser(tyro.conf.FlagConversionOff[RunViewer])  # noqa