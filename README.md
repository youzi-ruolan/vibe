# 观知 · 历史与科普短片流水线

默认生成 **1080×1920、30 帧、42 秒**竖屏动态图形视频，只有背景音乐，没有 AI 旁白。画面保留精简知识文字。

## 本次升级

- 暖纸色、墨黑、朱红的编辑式视觉；逐镜头构图、图解与进度分章。
- 真正的前后镜头叠化，配合位移和缓动；镜头内持续运动。
- 分析 BGM 的短时能量变化，在目标切点附近寻找音乐节点。不是固定 BPM 的机械卡点。
- 自动识别 `assets/千年之后(氛围版).mp3`，兼容中文全角括号。
- 音乐循环、响度处理、首尾淡入淡出，严格匹配视频长度。
- 先检查音乐和 FFmpeg，再开始渲染；直接输出编码视频，避免产生几千张 PNG。
- 正式目录包含 20 个历史案例和 3 个原有科普/企业史主题，已移除社保内容。

## 快速生成

双击 `一键输入主题生成.bat` 选择主题，或执行：

```bat
python pipeline.py --topic paper_history
```

首条精编样片为 `output/paper_history/final.mp4`，配有封面、分镜总览、来源与元数据。

```bat
python pipeline.py --topic printing_history --duration 42
python pipeline.py --topic paper_history --bgm "D:\music\背景音乐.mp3" --music-start 12
```

FFmpeg 会自动查找 Downloads 下的 `ffmpeg*/bin/ffmpeg.exe`，也可用 `--ffmpeg` 指定。首次运行需安装 `requirements.txt` 中的依赖及 Playwright Chromium。默认不生成语音；仅在需要时加 `--with-voice`。

## 案例与分镜

历史目录：`topics/history_cases.json`。20 个 ID：

paper_history、printing_history、compass_history、gunpowder_history、steam_history、railway_history、telegraph_history、telephone_history、electricity_history、automobile_history、aviation_history、vaccination_history、penicillin_history、spaceflight_history、internet_history、smartphone_history、renewable_history、urban_history、democracy_history、maritime_history。

其他主题：browser_rendering、frontend_stack、tesla_history。

`topics/storyboards.json` 提供精编分镜。当前纸张主题包含 8 个专门设计的镜头：纸张悬浮、竹简、纤维成纸、纸页展开、传播路线、印刷复制、知识网络、结尾。其他主题根据事实点自动生成通用图解镜头；可以继续在这里逐条精编。

这是原创动态图形样片，不包含真人、AI 写实影像或下载的历史实拍；不是联网抓取热门榜单的系统。历史说明为概述，来源会随片输出，发布前应核对资料与音乐使用范围。

## 输出

- `final.mp4`：带背景音乐成片
- `silent.mp4`：画面母版
- `cover.jpg` / `detail.jpg`：封面与详情帧
- `storyboard.jpg`：首条样片的分镜总览（验证工具生成）
- `metadata.json`：实际镜头起止、音乐文件、能量变化与内容
- `SOURCES.txt`：参考来源
- `narration.txt`：参考文稿，不会自动朗读
- `render.log`：画面编码日志

画面检查：`python verify_render.py`，覆盖 23 个主题的所有镜头及首条样片转场。
