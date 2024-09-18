"""Prepross panel for the viewer"""
"""(In Progress: JiChen)"""

# from __future__ import annotations

from pathlib import Path
import subprocess
import os
import zipfile
import viser
import viser.transforms as vtf
from typing_extensions import Literal

from nerfstudio.data.scene_box import OrientedBox
from nerfstudio.models.base_model import Model
from nerfstudio.models.splatfacto import SplatfactoModel



def populate_preprocess_tab(
    server: viser.ViserServer,
) -> None:

    with server.gui.add_folder("Upload Images"):
        populate_upload_images_tab(server)
    with server.gui.add_folder("Upload Video"):
        populate_upload_video_tab(server)
    with server.gui.add_folder("Filter blurred images", expand_by_default=False):
        populate_filter_blurred_image_tab(server)
    with server.gui.add_folder("Colmap"):
        populate_colmap_tab(server)


# 上傳圖片欄位
def populate_upload_images_tab(
    server: viser.ViserServer,
) -> None:
    # server.gui.add_markdown("<small>上傳圖集(.zip)</small> ")
    input_dir = server.gui.add_text("Name of Dataset", initial_value="dataset_name")
    gui_upload_button = server.gui.add_upload_button(
        "Upload", icon=viser.Icon.UPLOAD
    )
    @gui_upload_button.on_upload
    def _(_) -> None:
        """Callback for when a file is uploaded."""
        file = gui_upload_button.value
        print(file.name, len(file.content), "bytes")
        if file:
            file_name = file.name
            file_content = file.content
            # 儲存檔案到指定目錄
            # 指定要儲存檔案的目錄
            current_directory = os.path.dirname(os.path.abspath(__file__))
            # 獲取 'nerfstudio' 的父目錄
            project_root = os.path.abspath(os.path.join(current_directory, '..', '..'))
            save_directory = os.path.join(project_root, 'dataset', input_dir.value)

            # 確保目錄存在，若不存在則創建
            if not os.path.exists(save_directory):
                os.makedirs(save_directory)

            # 儲存上傳的 zip 檔案
            zip_file_path = os.path.join(save_directory, file.name)
            with open(zip_file_path, 'wb') as f:
                f.write(file.content)
        
            print(f"ZIP file '{file.name}' saved successfully at '{zip_file_path}'")

            try:
                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    # 解壓縮到同一個目錄
                    zip_ref.extractall(save_directory)
                print(f"ZIP file '{file.name}' extracted successfully to '{save_directory}'")

                # 解壓縮後刪除 .zip 檔案
                os.remove(zip_file_path)
                print(f"ZIP file '{file.name}' deleted successfully.")

            except zipfile.BadZipFile:
                print(f"Error: '{file.name}' is not a valid zip file.")
        else:
            print("No file uploaded.")

# 上傳影片欄位
def populate_upload_video_tab(
    server: viser.ViserServer,
) -> None:
    # server.gui.add_markdown("<small>上傳影片</small> ")
    input_dir = server.gui.add_text("Name of Dataset", initial_value="dataset_name")
    gui_upload_button = server.gui.add_upload_button(
        "Upload", icon=viser.Icon.UPLOAD
    )
    @gui_upload_button.on_upload
    def _(_) -> None:
        """Callback for when a file is uploaded."""
        file = gui_upload_button.value
        print(file.name, len(file.content), "bytes")
        if file:
            file_name = file.name
            file_content = file.content
            # 儲存檔案到指定目錄
            # 指定要儲存檔案的目錄
            current_directory = os.path.dirname(os.path.abspath(__file__))
            # 獲取 'nerfstudio' 的父目錄
            project_root = os.path.abspath(os.path.join(current_directory, '..', '..'))
            save_directory = os.path.join(project_root, 'dataset', input_dir.value)

            # 確保目錄存在，若不存在則創建
            if not os.path.exists(save_directory):
                os.makedirs(save_directory)

            # 儲存檔案
            file_path = os.path.join(save_directory, file_name)
            with open(file_path, 'wb') as f:
                f.write(file_content)
        
            print(f"Video '{file_name}' saved successfully at '{file_path}'")
        else:
            print("No file uploaded.")

# 模糊影像處理欄位
def populate_filter_blurred_image_tab(
    server: viser.ViserServer,
) -> None:
    server.gui.add_markdown("<small>過濾輸入的圖片集</small> ")
    image_num = server.gui.add_text("Num of Images:", initial_value="0")
    thresholding = server.gui.add_slider(
                    "Thresholding",
                    0.0,
                    10.0,
                    step=0.1,
                    initial_value=2.5,
                )
    blurred_image_num = server.gui.add_text("Num of Images:", initial_value="0")
    filter_blurred_images = server.gui.add_button("Filter Blurred Image", icon=viser.Icon.TERMINAL_2)
    @filter_blurred_images.on_click
    def _(event: viser.GuiEvent) -> None:
        assert event.client is not None

    delete_blurred_images = server.gui.add_button("Delete Blurred Image", icon=viser.Icon.TERMINAL_2)
    @delete_blurred_images.on_click
    def _(event: viser.GuiEvent) -> None:
        assert event.client is not None

    fix_blurred_images = server.gui.add_button("Fix Blurred Image", icon=viser.Icon.TERMINAL_2)
    @fix_blurred_images.on_click
    def _(event: viser.GuiEvent) -> None:
        assert event.client is not None

def populate_colmap_tab(
    server: viser.ViserServer,
) -> None:
    # GUI 界面说明
    colmap_tab_markdown = server.gui.add_markdown("<small>進行Colmap，生成點雲</small> ")

    # 獲取dataset資料夾中的所有子文件夾名稱
    dataset_path = "dataset"  # 假設dataset目錄路徑是 "dataset"
    folder_names = [f for f in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, f))]
    
    # 添加Button Group，讓用戶選擇要處理的是圖片還是影片
    #button_group = server.gui.add_button_group("選擇處理類型：", ["Images", "Video"])

    # 添加一個下拉式選單來讓用戶選擇處理類型：圖片或影片
    content_type_dropdown = server.gui.add_dropdown(
        "選擇處理類型：", 
        options=["images", "video"],  # 下拉選單的選項
        initial_value="images"  # 默認值
    )

    # 监听下拉选单更改事件
    @content_type_dropdown.on_update
    def _(event: viser.GuiEvent) -> None:
        print(content_type_dropdown.value)

    # 添加一個下拉選單，讓用戶選擇資料夾
    selected_folder = server.gui.add_dropdown("Select Dataset Folder", options=folder_names)

    # Run Colmap 按鈕
    run_colmap = server.gui.add_button("Run Colmap", icon=viser.Icon.TERMINAL_2)

    # 按鈕點擊事件
    @run_colmap.on_click
    def _(event: viser.GuiEvent) -> None:
        assert event.client is not None

        # 獲取用戶選擇的資料夾名稱
        chosen_folder = selected_folder.value
        colmap_input_path = os.path.join(dataset_path, chosen_folder)
        processed_data_dir = os.path.join(colmap_input_path, "colmap_processed")

        # 驗證路徑是否有效
        if not os.path.exists(colmap_input_path):
            server.gui.add_markdown("<small style='color:red;'>無效的目錄路徑，請重新檢查。</small>")
            return

        # 提示用戶正在運行 COLMAP
        server.gui.add_markdown(f"<small>正在運行 COLMAP 以處理 {content_type_dropdown.value}，請稍等...</small>")

        # 構建 COLMAP 命令
        colmap_command = [
            "ns-process-data",
            content_type_dropdown.value,
            "--data", colmap_input_path,
            "--output-dir", processed_data_dir
        ]

        print(colmap_command)

        try:
            result = subprocess.run(colmap_command, check=True, capture_output=True, text=True)
            print("Success:", result.stdout)
        except subprocess.CalledProcessError as e:
            print("Command failed with return code", e.returncode)
            print("Output:", e.stdout)
            print("Error:", e.stderr)
        except FileNotFoundError:
            print("The command or file was not found.")
        except Exception as e:
            print("An unexpected error occurred:", str(e))
