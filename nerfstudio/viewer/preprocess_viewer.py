import viser
import os
import subprocess
from nerfstudio.viewer.preprocess_panel import populate_preprocess_tab 
from nerfstudio.viewer.viewer_elements import (
    ViewerButtonGroup,
    ViewerCheckbox,
    ViewerDropdown,
    ViewerElement,
    ViewerNumber,
    ViewerRGB,
    ViewerSlider,
    ViewerVec3,
)

class PreprocessViewer:
    def __init__(self):
        """初始化 Viser 伺服器並設置場景"""
        # 創建 Viser 伺服器
        self.server = viser.ViserServer()

        self.server.gui.configure_theme(
            #titlebar_content=titlebar_theme,
            control_layout="collapsible",
            dark_mode=True,
            brand_color=(255, 211, 105),
        )

        # 添加一個按鈕來刷新資料夾列表
        self.refresh_button = self.server.gui.add_button("Refresh Dataset List", icon=viser.Icon.REFRESH)
        self.refresh_button.on_click(self.on_refresh_button_click)
        # 獲取當前項目的根目錄
        current_directory = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_directory, '..', '..'))

        # dataset 目錄路徑
        self.dataset_directory = os.path.join(project_root, 'dataset')

        # 確保 dataset 目錄存在
        if not os.path.exists(self.dataset_directory):
            os.makedirs(self.dataset_directory)

        # 生成樹狀結構的 Markdown
        dataset_tree_markdown = self.generate_tree_markdown(self.dataset_directory)
        # 使用 Viser 的 add_markdown 將資料樹顯示到 GUI 中
        self.markdown_handle = self.server.gui.add_markdown(f"""
        {dataset_tree_markdown}
        """)
        
        # 獲取 dataset 目錄下有 colmap_processed 資料夾的子文件夾列表
        folder_names = self.get_valid_dataset_folders()
        self.selected_folder = self.server.gui.add_dropdown("Select Dataset", options=folder_names)
        method_names = ["splatfacto", "BadGaussian?", "XXXX?", "DN-splatter?"]
        self.selected_method = self.server.gui.add_dropdown("Select Method", options=method_names)

        # 添加 "Train" 按鈕
        self.train_button = self.server.gui.add_button(
            label="Train",
            icon=viser.Icon.ARROW_BIG_UP_LINES,  # 使用圖標
            color="gray",
            hint="Select Training Method and Dataset Folder Before Training",  # 提示信息
        )

        # 綁定按鈕點擊事件
        self.train_button.on_click(self.on_train_button_click)

        tabs = self.server.gui.add_tab_group()
        with tabs.add_tab("Preprocess", viser.Icon.PACKAGE_EXPORT):
            populate_preprocess_tab(self.server, self)

    def on_train_button_click(self, _):
        """處理按鈕點擊事件，執行訓練操作"""
        print("Training started...")

        dataset_folder = self.selected_folder.value
        method = self.selected_method.value

        if not dataset_folder or not method:
            print("Please select both a dataset folder and a training method.")
            return
        
        # 組合命令
        dataset_path = os.path.join(self.dataset_directory, dataset_folder, "colmap_processed")
        command = f"ns-train {method} --data {dataset_path}"

        print(f"Executing command: {command}")

        # 使用 subprocess 執行命令
        try:
            # result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.show_modal("Start Training , You can view the process at: [http://0.0.0.0:7007](http://0.0.0.0:7007)")
            # 持续读取子进程的 stdout 和 stderr 并实时打印
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            
            # 确保所有输出被读取完毕
            stderr = process.communicate()[1]
            if stderr:
                print(f"Error: {stderr}")
            print("Training finished!")
        except subprocess.CalledProcessError as e:
            print(f"Training failed: {e}")

    def show_modal(self, title: str):
        """显示模态窗口"""
        modal_handle = self.server.gui.add_modal(title=title)

    
    def on_refresh_button_click(self, _):
        """處理按鈕點擊事件，刷新dataset tree"""
        self.update_markdown()

    def update_markdown(self):
        """更新 Markdown 内容以显示最新的目錄樹。"""
        markdown_content = self.generate_tree_markdown(self.dataset_directory)

        # 假设你有一个 GuiMarkdownHandle 对象来显示 Markdown
        if self.markdown_handle:
            self.markdown_handle.content = markdown_content
        else:
            # 如果没有现有的 Markdown 组件，则添加一个新的
            self.markdown_handle = self.add_markdown(content=markdown_content)
    
    def run(self):
        """启动 Viser 伺服器"""
        print("Viser server is running. Open the following URL in your browser to view the GUI.")
        share_url = self.server.request_share_url()
        if share_url:
            print(share_url)
        else:
            print("Failed to obtain share URL.")
    
        # Keep the script running to keep the server alive
        try:
            while True:
                pass  # Replace with server operations if needed
        except KeyboardInterrupt:
            self.server.stop()  # Gracefully stop the server on interrupt

    def generate_tree_markdown(self, directory: str, parent_id: str = '') -> str:
        """遞迴遍歷目錄，生成樹狀結構的 GUI 元件內容。"""
        elements = []
        level = parent_id.count('_')  # 根據 parent_id 的下劃線數量來判斷層級

        indent = "　" * level  # 用縮進來模擬層級結構

        # 列出目錄中的所有項目
        entries = os.listdir(directory)

        # 分別列出文件和文件夾
        files = [entry for entry in entries if os.path.isfile(os.path.join(directory, entry))]
        folders = [entry for entry in entries if os.path.isdir(os.path.join(directory, entry))]

        # 排序文件和文件夾
        files.sort()
        folders.sort()

        # 先處理文件
        for entry in files:
            path = os.path.join(directory, entry)
            elements.append(f"""
            {indent}- {entry}
            """)

        # 再處理文件夾
        for entry in folders:
            path = os.path.join(directory, entry)
            folder_id = f"{parent_id}_{entry}"
            elements.append(f"""
            <details>
            <summary>{indent}📁 {entry}</summary>
            {self.generate_tree_markdown(path, folder_id)}
            </details>""")

        return "\n".join(elements)
    
    def get_valid_dataset_folders(self):
        """獲取 dataset 目錄中包含 colmap_processed 資料夾的子文件夾列表"""
        valid_folders = []
        
        # 遍歷 dataset 目錄中的所有子文件夾
        for folder_name in os.listdir(self.dataset_directory):
            folder_path = os.path.join(self.dataset_directory, folder_name)
            # 檢查是否是資料夾，且其下是否有 colmap_processed 資料夾
            if os.path.isdir(folder_path) and os.path.exists(os.path.join(folder_path, 'colmap_processed')):
                valid_folders.append(folder_name)
        
        return valid_folders
    
    def refresh_dataset_list(self):
        """刷新 dataset 資料夾列表及 GUI 下拉框"""
        # 獲取 dataset 目錄下有 colmap_processed 資料夾的子文件夾列表
        folder_names = self.get_valid_dataset_folders()
        
        # 更新 Select Dataset 下拉框的選項
        self.selected_folder.options = folder_names

        # 顯示已刷新資料夾列表
        print(f"Dataset folders refreshed: {folder_names}")