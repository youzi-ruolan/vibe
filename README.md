# 观知 · 历史与科普短片流水线

默认生成 **1080×1920、30 帧、至少 42 秒**竖屏动态图形视频，只有背景音乐，没有 AI 旁白。画面保留精简知识文字；阅读时间不足时自动延长。

## 本次升级

- 暖纸色、墨黑、朱红的编辑式视觉；逐镜头构图、图解与进度分章。
- 真正的前后镜头叠化，配合位移和缓动；镜头内持续运动。
- 分析 BGM 的短时能量变化，在目标切点附近寻找音乐节点。不是固定 BPM 的机械卡点。
- 自动识别 `assets/千年之后(氛围版).mp3`，兼容中文全角括号。
- 音乐循环、响度处理、首尾淡入淡出，严格匹配视频长度。
- 先检查音乐和 FFmpeg，再开始渲染；直接输出编码视频，避免产生几千张 PNG。
- 正式目录包含 23 个历史案例和 3 个原有科普/企业史主题，已移除社保内容。
- 全部 26 个主题都有单独精编的分镜、动画节点和因果推进，不再把事实段落直接套进统一标题。
- 先确定每镜阅读时间，再在剩余空间寻找音乐切点，避免为卡点牺牲理解。
- 生成前检查内容字段、图解节点、来源链接、阅读时间和文字排版；输出结构检查报告。结构检查不代表自动验证事实或叙事质量。
- 导出后完整解码，并检查视频、音乐均存在；检测时长、画面尺寸及音画长度。不通过则保留上一版成片。

## 快速生成

双击 `一键输入主题生成.bat` 选择主题，或执行：

```bat
python pipeline.py --topic paper_history
```

首条精编样片为 `output/paper_history/final.mp4`，配有封面、分镜总览、来源与元数据。

```bat
python pipeline.py --topic printing_history --duration 42
python pipeline.py --topic paper_history --bgm "D:\music\背景音乐.mp3" --music-start 12
python pipeline.py --topic steam_history --check-only
```

FFmpeg 会自动查找 Downloads 下的 `ffmpeg*/bin/ffmpeg.exe`，也可用 `--ffmpeg` 指定。首次运行需安装 `requirements.txt` 中的依赖及 Playwright Chromium。默认不生成语音；仅在需要时加 `--with-voice`。

## 案例与分镜

历史目录：`topics/history_cases.json`。23 个 ID：

paper_history、printing_history、compass_history、gunpowder_history、steam_history、railway_history、telegraph_history、telephone_history、electricity_history、automobile_history、aviation_history、vaccination_history、penicillin_history、spaceflight_history、internet_history、smartphone_history、renewable_history、urban_history、democracy_history、maritime_history、an_lushan_history、five_dynasties_history、song_unification_history。

其他主题：browser_rendering、frontend_stack、tesla_history。

`topics/storyboards.json` 提供全部 26 个主题的精编分镜。新增安史之乱与藩镇、五代十国、宋初统一三个中国古代史主题，使用区域关系示意和五代更替动画；擦除转场采用斜向推进与短暂强调线。纸张主题包含 8 个专门设计的镜头：纸张悬浮、竹简、纤维成纸、纸页展开、传播路线、印刷复制、知识网络、结尾。其余主题各有 6 个镜头，通过主题专属的时间线、过程示意与关系网络讲解。

每条片子的制作顺序是：来源与事实 → 问题开场 → 解释机制 → 扩展与影响 → 回答开头的问题 → 分配阅读时间 → 音乐切点微调 → 动画与转场 → 画面检查 → 编码输出。

新增主题需要同时补充目录事实与精编分镜。分镜字段包括 `role`、`kicker`、`title`、`body`、`visual`、`nodes`、`transition` 和 `weight`。`role` 记录叙事作用；不是由程序自动理解或保证因果关系。图解用于说明过程与关系，不把示意图当作真实机械结构或史料图像。

## 是否需要大模型

当前预置内容运行时不需要 API、密钥或额外模型服务，也不会自动上传音乐和文稿。以后如需“任意主题自动找资料、写稿和设计分镜”，可以加入可选的大模型写稿阶段，生成同样的分镜数据，再进入当前检查与渲染阶段。资料核验、叙事审阅和最终画面检查仍然需要保留；仅接入模型不能保证高质量成片。

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
- `quality_report.json`：生成过程的结构、时序与画面检查结果
- `preflight_report.json`：`--check-only` 的检查结果，不覆盖已有视频元数据

画面检查：`python verify_render.py`，覆盖全部 26 个主题的所有镜头和转场、文字溢出、阅读时长、密集音乐切点及过短时长拒绝，并生成纸张和蒸汽机两个主题的画面总览。
