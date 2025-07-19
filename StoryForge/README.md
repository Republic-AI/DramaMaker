# 韩漫插画生成器

一个简单的韩漫风格插画生成系统，基于 OpenAI DALL-E 3。

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install openai requests
```

### 2. 准备文件
确保以下文件存在：
- `examples/ryan_story.txt` - 故事文本
- `examples/ryan_npc.yaml` - 角色信息
- `manga_sample/ryan_oid_room.png.json` - 房间对象信息

### 3. 生成分镜
```bash
cd src
python manga_sty_parser.py
```

### 4. 生成插画
```bash
python manga_gen.py
```

## 📁 文件结构

```
StoryForge/
├── src/
│   ├── manga_sty_parser.py    # 故事分镜生成
│   └── manga_gen.py          # 插画生成
├── examples/
│   ├── ryan_story.txt        # 故事文本
│   └── ryan_npc.yaml        # 角色信息
├── manga_sample/
│   ├── ryan_avatar.png      # 角色头像
│   ├── ryan_oid_room.png    # 房间图片
│   └── ryan_oid_room.png.json # 房间对象信息
└── output/                  # 生成结果
    ├── segmented_scenes.json # 分镜结果
    └── main_illustrations_output.json # 插画结果
```

## 🎨 核心功能

### 故事分镜 (`manga_sty_parser.py`)
- 将自然语言故事分解为视觉场景
- 结合角色信息和房间对象
- 输出结构化的分镜数据

### 插画生成 (`manga_gen.py`)
- 基于分镜生成韩漫风格插画
- 使用改进的 prompt 模板
- 保持风格一致性

## 🔧 自定义

### 修改 Prompt 模板
在 `manga_gen.py` 中的 `build_main_illustration_prompt` 函数修改：

```python
prompt = f"""
Create a full-color 1:1 high-resolution Korean romance manga illustration.

STYLE: in the exact style of Light and Night official character art, Korean romance manga with soft pastel palette, elegant line art, dreamy atmosphere

SCENE: {scene.get('short description', '')}
CHARACTER: perfectly centered, waist-up portrait, well-lit from front, soft romantic lighting, interacting with {scene.get('object', '')}

POSITIVE: soft elegant colors, dreamy atmosphere, young-female aesthetic, romantic lighting, Korean manga style, delicate line art, soft pastel palette
NEGATIVE: monochrome, grayscale, black and white, western cartoon, painterly brush, 3D render, off-center, corner placement, dark lighting

Story context: {scene.get('full_story', '')} ({scene.get('scene_position', '')})
"""
```

### 添加新的故事
1. 创建新的故事文件（如 `examples/new_story.txt`）
2. 创建对应的角色信息文件
3. 修改 `manga_sty_parser.py` 中的文件路径

## 📝 使用示例

### 默认故事
Ryan 尝试烹饪但遇到困难，烧焦了食物很沮丧，然后决定休息看书平静下来。

### 生成流程
1. **分镜生成**：故事被分解为 2 个场景
   - 场景 1：Ryan 在炉子旁烹饪，看起来很沮丧
   - 场景 2：Ryan 在沙发上读书，平静下来

2. **插画生成**：每个场景生成对应的韩漫风格插画

## 🎯 特点

- **风格一致**：使用改进的 prompt 模板确保韩漫风格
- **构图优化**：强调人物居中、腰部以上构图
- **色彩控制**：柔和色彩，避免过于鲜艳
- **简单易用**：只需运行两个 Python 脚本

## 🔑 API 密钥

在 `manga_gen.py` 中设置你的 OpenAI API 密钥：

```python
openai.api_key = "your-api-key-here"
```

## 📊 输出

- **分镜结果**：`output/segmented_scenes.json`
- **插画结果**：`output/main_illustrations_output.json`
- **生成的图片**：保存在 `output/` 目录