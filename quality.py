"""Structural and readability checks, not an automated fact or logic verifier."""
import math
import re

VISUALS = {'paper', 'bamboo', 'fibers', 'sheets', 'press', 'route',
           'network', 'timeline', 'mechanism', 'orbit', 'regions', 'succession'}


def reading_units(text):
    return len(re.findall(r'[A-Za-z0-9]+|[\u3400-\u9fff]', text))


def minimum_hold(scene):
    # Title and body partly overlap in reading; allow a further pause after entry.
    units = reading_units(scene['body']) + .5 * reading_units(scene['title'])
    return round(max(3.2, .9 + units / 7), 2)


def validate_plan(data, scenes, duration=None):
    if not 4 <= len(scenes) <= 16:
        raise ValueError('分镜需为 4–16 个，每个镜头只讲一个重点。')
    if not data.get('sources') or not all(s.get('url', '').startswith(('http://', 'https://')) for s in data['sources']):
        raise ValueError('主题缺少参考来源链接。')
    if scenes[0].get('role') != 'hook' or scenes[-1].get('role') != 'takeaway':
        raise ValueError('分镜需要问题开场和回应问题的结尾。')
    for i, scene in enumerate(scenes):
        for field, limit in [('title', 44), ('body', 120), ('kicker', 40)]:
            if not isinstance(scene.get(field), str) or not scene[field].strip() or len(scene[field]) > limit:
                raise ValueError(f'镜头 {i+1} 的 {field} 缺失或过长（上限 {limit} 字符）。')
        if scene.get('visual') not in VISUALS:
            raise ValueError(f'镜头 {i+1} 使用了未知动画类型。')
        if scene.get('transition', 'dissolve') not in {'wipe', 'dissolve'}:
            raise ValueError(f'镜头 {i+1} 使用了未知转场。')
        if not isinstance(scene.get('weight', 1), (int, float)) or not math.isfinite(scene.get('weight', 1)) or scene.get('weight', 1) <= 0:
            raise ValueError(f'镜头 {i+1} 的时长权重必须为正数。')
        if 'nodes' in scene and (len(scene['nodes']) != 3 or any(not isinstance(n, str) or not n or len(n) > 8 for n in scene['nodes'])):
            raise ValueError(f'镜头 {i+1} 应有 3 个不超过 8 字符的图解节点。')
    minimum = sum(minimum_hold(scene) for scene in scenes)
    if duration is not None and duration + .001 < minimum:
        raise ValueError(f'此主题至少需要 {math.ceil(minimum)} 秒供阅读，不能压缩到 {duration:g} 秒。')
    return {
        'structural_checks': 'passed',
        'scene_count': len(scenes),
        'minimum_duration': round(minimum, 2),
        'minimum_scene_holds': [minimum_hold(s) for s in scenes],
        'source_links_present': len(data['sources']),
        'fact_verification': 'not_automated',
        'semantic_logic_review': 'editorial_storyboard_required',
        'voice_mode': 'off_by_default',
    }
