# 韩漫插画生成器 - 同事使用指南

这是一个简化的韩漫风格插画生成系统，专门为不懂代码的同事设计。系统会自动将故事分解为场景，然后生成风格一致的韩漫插画。

## 🎯 系统概述

### 核心文件
- **`src/manga_sty_parser.py`** - 故事分镜生成器
- **`src/manga_gen.py`** - 插画生成器（这是你需要主要修改的文件）

### 工作流程
1. 输入故事 → 2. 自动分镜 → 3. 生成插画 → 4. 保存结果

## 🚀 快速使用

### 第一步：生成分镜
```bash
cd src
python manga_sty_parser.py
```
这会读取 `examples/ryan_story.txt` 中的故事，生成分镜结果保存到 `output/segmented_scenes.json`

### 第二步：生成插画
```bash
python manga_gen.py
```
这会读取分镜结果，为每个场景生成韩漫插画，保存到 `output/` 目录

## 🔧 如何修改 Prompt（重要！）

如果你想要调整生成的插画风格，主要修改 `src/manga_gen.py` 文件中的 `build_main_illustration_prompt` 函数：

### 当前 Prompt 模板（第 35-50 行）
```python
prompt = f"""
Create a full-color 1:1 high-resolution Korean romance manga illustration.

STYLE: in the exact style of Light and Night official character art, Korean romance manga with soft pastel palette, elegant line art, dreamy atmosphere

SCENE: {scene.get('short description', '')}
CHARACTER: perfectly centered, waist-up portrait, well-lit from front, soft romantic lighting, interacting with {scene.get('object', '')}
OBJECTS: {objects_str}

POSITIVE: soft elegant colors, dreamy atmosphere, young-female aesthetic, romantic lighting, Korean manga style, delicate line art, soft pastel palette
NEGATIVE: monochrome, grayscale, black and white, western cartoon, painterly brush, 3D render, off-center, corner placement, dark lighting

Story context: {scene.get('full_story', '')} ({scene.get('scene_position', '')})
"""
```

### 修改建议

#### 1. 调整风格描述
- **更韩漫风格**：在 `STYLE` 行添加更多韩漫关键词
- **更浪漫风格**：在 `POSITIVE` 行添加 `romantic, dreamy, soft lighting`
- **更现代风格**：在 `STYLE` 行改为 `modern Korean webtoon style`

#### 2. 调整构图要求
- **全身构图**：将 `waist-up portrait` 改为 `full body shot`
- **特写构图**：将 `waist-up portrait` 改为 `close-up portrait`
- **侧面构图**：添加 `side view, profile shot`

#### 3. 调整色彩要求
- **更鲜艳**：在 `POSITIVE` 行添加 `vibrant colors, bright palette`
- **更柔和**：在 `POSITIVE` 行添加 `muted colors, soft palette`
- **特定色彩**：添加 `pink tones, pastel blue, warm lighting`

### 示例修改

#### 更现代的韩漫风格：
```python
STYLE: in the exact style of modern Korean webtoon, clean line art, vibrant colors, dynamic composition
```

#### 更浪漫的少女风格：
```python
POSITIVE: soft elegant colors, dreamy atmosphere, young-female aesthetic, romantic lighting, Korean manga style, delicate line art, soft pastel palette, sparkles, flowers, soft blush
```

## 📁 文件结构说明

```
StoryForge/
├── src/
│   ├── manga_sty_parser.py    # 故事分镜（一般不需要修改）
│   └── manga_gen.py          # 插画生成（主要修改文件）
├── examples/
│   ├── ryan_story.txt        # 故事文本（可以修改）
│   └── ryan_npc.yaml        # 角色信息（可以修改）
├── manga_sample/
│   ├── ryan_avatar.png      # 角色头像
│   ├── ryan_oid_room.png    # 房间图片
│   └── ryan_oid_room.png.json # 房间对象信息
└── output/                  # 生成结果
    ├── segmented_scenes.json # 分镜结果
    └── main_illustrations_output.json # 插画结果
```

## 🎨 如何添加新故事

### 方法1：修改现有故事
编辑 `examples/ryan_story.txt` 文件，替换里面的故事内容。

### 方法2：创建新故事
1. 创建新的故事文件，如 `examples/new_story.txt`
2. 修改 `src/manga_sty_parser.py` 第 130 行：
   ```python
   story_path = os.path.join(base_dir, '../examples/new_story.txt')
   ```

## 🔑 API 密钥设置

在 `src/manga_gen.py` 第 6 行设置你的 OpenAI API 密钥：
```python
openai.api_key = "your-api-key-here"
```

## 📊 输出文件说明

### 分镜结果 (`output/segmented_scenes.json`)
```json
[
  {
    "sequence_id": 1,
    "short description": "Ryan 在炉子旁烹饪，看起来很沮丧",
    "object": "stove",
    "scene_position": "beginning"
  }
]
```

### 插画结果 (`output/main_illustrations_output.json`)
```json
[
  {
    "sequence_id": 1,
    "main_illustration_path": "output/main_illustration_1.png",
    "main_illustration_prompt": "使用的完整 prompt"
  }
]
```

## 🎯 常见问题

### Q: 生成的图片风格不一致怎么办？
A: 修改 `manga_gen.py` 中的 `STYLE` 和 `POSITIVE` 部分，确保风格描述更具体。

### Q: 人物构图不好怎么办？
A: 修改 `CHARACTER` 行，添加更具体的构图要求，如 `perfectly centered, waist-up portrait`。

### Q: 颜色不够韩漫风格怎么办？
A: 在 `POSITIVE` 行添加更多韩漫色彩关键词，如 `soft pastel palette, Korean manga colors`。

### Q: 想要不同的故事怎么办？
A: 修改 `examples/ryan_story.txt` 文件内容，然后重新运行分镜生成。

## 🚀 使用步骤总结

1. **准备故事**：编辑 `examples/ryan_story.txt`
2. **调整风格**：修改 `src/manga_gen.py` 中的 prompt 模板
3. **生成分镜**：运行 `python manga_sty_parser.py`
4. **生成插画**：运行 `python manga_gen.py`
5. **查看结果**：在 `output/` 目录查看生成的图片

## 💡 提示

- 每次修改 prompt 后，需要重新运行 `python manga_gen.py` 才能看到效果
- 可以保存多个版本的 prompt 模板，方便对比效果
- 生成的图片会自动保存到 `output/` 目录
- 如果 API 调用失败，检查网络连接和 API 密钥是否正确