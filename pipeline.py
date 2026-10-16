"""Deterministic motion graphics with music-aware scene timing."""
import argparse
import asyncio
import base64
import json
import math
import os
from array import array
from pathlib import Path
import shutil
import subprocess
from playwright.sync_api import sync_playwright
from quality import minimum_hold, validate_plan

ROOT = Path(__file__).resolve().parent
CAT = {}
for catalog in ('catalog.json', 'history_cases.json'):
    CAT.update(json.loads((ROOT / 'topics' / catalog).read_text(encoding='utf-8')))


def find_ffmpeg(requested):
    if Path(requested).is_file() or shutil.which(requested):
        return str(requested)
    candidates = sorted((Path.home() / 'Downloads').glob('ffmpeg*/bin/ffmpeg.exe'))
    if candidates:
        return str(candidates[-1])
    raise ValueError('找不到 FFmpeg，请用 --ffmpeg 指定路径。')


def find_bgm(requested):
    if requested:
        music = Path(requested).expanduser().resolve()
        if not music.is_file():
            raise ValueError(f'找不到背景音乐：{music}')
        return music
    for music in sorted((ROOT / 'assets').glob('*.mp3')):
        if music.stem.replace('（', '(').replace('）', ')') == '千年之后(氛围版)':
            return music
    raise ValueError('请将《千年之后（氛围版）》MP3 放入 assets，或使用 --bgm 指定音乐。')


def music_analysis(ffmpeg, music, duration, start):
    """Short-time RMS transients suggest cuts; this does not infer a fixed BPM."""
    raw = subprocess.check_output([ffmpeg, '-v', 'error', '-stream_loop', '-1',
        '-ss', str(start), '-i', str(music), '-t', str(duration), '-vn', '-ac', '1',
        '-ar', '8000', '-f', 's16le', '-'])
    pcm = array('h', raw)
    energy = [math.sqrt(sum(v*v for v in pcm[i:i+400]) / len(pcm[i:i+400])) / 32768
              for i in range(0, len(pcm), 400)]
    onsets = []
    for i in range(2, len(energy)-2):
        baseline = sum(energy[max(0, i-8):i]) / min(i, 8)
        strength = energy[i] - baseline
        if strength > .012 and energy[i] >= max(energy[i-1], energy[i+1]):
            onsets.append((i * .05, strength))
    peaks = []
    for t, strength in sorted(onsets, key=lambda item: item[1], reverse=True):
        if all(abs(t-p) > .32 for p in peaks):
            peaks.append(t)
    return energy, sorted(peaks)


def storyboard(key, data, duration, peaks):
    boards = json.loads((ROOT / 'topics' / 'storyboards.json').read_text(encoding='utf-8'))
    scenes = boards.get(key)
    if scenes is None:
        raise ValueError('主题缺少精编分镜，请先补充 topics/storyboards.json。')
    validate_plan(data, scenes, duration)
    scenes = [dict(s) for s in scenes]
    weights = [s.pop('weight', 1) for s in scenes]
    holds = [minimum_hold(s) for s in scenes]
    surplus = max(0, duration-sum(holds))
    lengths = [hold+surplus*weight/sum(weights) for hold,weight in zip(holds,weights)]
    cuts, target = [0.0], 0.0
    for i, length in enumerate(lengths[:-1]):
        target += length
        lower, upper = cuts[-1]+holds[i], duration-sum(holds[i+1:])
        candidates = [p for p in peaks if abs(p-target) <= .4 and lower <= p <= upper]
        cuts.append(min(candidates, key=lambda p: abs(p-target)) if candidates else max(lower,min(upper,target)))
    for i, scene in enumerate(scenes):
        scene['start'] = cuts[i]
        scene['end'] = cuts[i+1] if i+1 < len(cuts) else duration
    return scenes


async def tts(text, voice, target):
    import edge_tts
    await edge_tts.Communicate(text, voice).save(str(target))


def verify_output(ffmpeg, path, expected_duration, fps):
    # Decode the completed file, not just trust the encoder's successful exit.
    subprocess.run([ffmpeg, '-v', 'error', '-xerror', '-i', str(path),
        '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-'],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
    result = {'full_decode': 'passed', 'video_and_audio_present': True}
    probe_name = 'ffprobe.exe' if os.name == 'nt' else 'ffprobe'
    probe = Path(ffmpeg).with_name(probe_name)
    probe = str(probe) if probe.is_file() else shutil.which(probe_name)
    if probe:
        info = json.loads(subprocess.check_output([probe, '-v', 'error', '-show_streams',
            '-show_format', '-of', 'json', str(path)]))
        duration = float(info['format']['duration'])
        video = next(s for s in info['streams'] if s['codec_type'] == 'video')
        audio = next(s for s in info['streams'] if s['codec_type'] == 'audio')
        if abs(duration-expected_duration) > 1/fps+.01 or (video['width'], video['height']) != (1080,1920):
            raise RuntimeError('成片时长或画面尺寸不符合设定，已保留上一版成片。')
        if abs(float(audio['duration'])-float(video['duration'])) > 1/fps+.05:
            raise RuntimeError('成片音画长度不匹配，已保留上一版成片。')
        result.update(duration=duration, width=video['width'], height=video['height'],
                      video_codec=video['codec_name'], audio_codec=audio['codec_name'])
    return result


def main():
    ap = argparse.ArgumentParser(description='知识短片：音乐驱动的竖屏动态图形')
    ap.add_argument('--topic', choices=sorted(CAT))
    ap.add_argument('--bgm', help='默认自动识别 assets 中的千年之后（氛围版）MP3')
    ap.add_argument('--music-start', type=float, default=0, help='音乐起点，秒')
    ap.add_argument('--ffmpeg', default=os.environ.get('FFMPEG_EXE', 'ffmpeg.exe'))
    ap.add_argument('--fps', type=int, default=30)
    ap.add_argument('--duration', type=float, help='默认至少 42 秒，按阅读时间自动延长')
    ap.add_argument('--check-only', action='store_true', help='只检查分镜、音乐和时间安排，不导出视频')
    ap.add_argument('--with-voice', action='store_true', help='可选启用配音，默认关闭')
    ap.add_argument('--no-voice', action='store_true', help='兼容旧命令，禁用配音')
    ap.add_argument('--voice', default='zh-CN-YunxiNeural')
    args = ap.parse_args()
    if (args.duration is not None and (not math.isfinite(args.duration) or not 10 <= args.duration <= 300)) or not 12 <= args.fps <= 60 or not math.isfinite(args.music_start) or args.music_start < 0:
        ap.error('时长需在 10–300 秒，帧率需在 12–60，音乐起点不能为负数。')
    if not args.topic:
        for key, data in CAT.items():
            print(f'{key:24} {data["title"]}')
        args.topic = input('\n输入主题 ID：').strip()
    if args.topic not in CAT:
        ap.error('未知主题 ID')
    try:
        ffmpeg, music = find_ffmpeg(args.ffmpeg), find_bgm(args.bgm)
    except ValueError as error:
        ap.error(str(error))
    data = dict(CAT[args.topic])
    try:
        boards = json.loads((ROOT/'topics'/'storyboards.json').read_text(encoding='utf-8'))
        report = validate_plan(data, boards.get(args.topic, []), args.duration)
        if args.duration is None:
            args.duration = max(42, math.ceil(report['minimum_duration']))
    except ValueError as error:
        ap.error(str(error))
    energy, peaks = music_analysis(ffmpeg, music, args.duration, args.music_start)
    data.update(duration=args.duration, scenes=storyboard(args.topic, data, args.duration, peaks),
                energy=energy, music={'file': music.name, 'start': args.music_start})
    out = ROOT / 'output' / args.topic
    out.mkdir(parents=True, exist_ok=True)
    report.update(duration=args.duration, fps=args.fps, music_file=music.name,
                  scheduled_holds=[round(s['end']-s['start'], 3) for s in data['scenes']],
                  render_checks='not_run')
    if args.check_only:
        (out/'preflight_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'分镜与时序检查通过：{len(data["scenes"])} 镜头，{args.duration:g} 秒；{out / "preflight_report.json"}')
        return
    (out/'quality_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'metadata.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'SOURCES.txt').write_text(data['title']+'\n'+data.get('disclaimer', '')+'\n\n参考来源：\n'+
        '\n'.join(f"{s['name']}\n{s['url']}" for s in data['sources']), encoding='utf-8')
    (out / 'narration.txt').write_text(data['narration'], encoding='utf-8')
    silent = out / 'silent.mp4'
    total = round(args.fps * args.duration)
    encode = [ffmpeg, '-y', '-v', 'error', '-f', 'image2pipe', '-vcodec', 'mjpeg',
        '-framerate', str(args.fps), '-i', '-', '-an', '-c:v', 'libx264', '-crf', '18',
        '-preset', 'fast', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(silent)]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={'width':1080, 'height':1920}, device_scale_factor=1)
            page.goto((ROOT/'public'/'index.html').as_uri())
            page.evaluate('(d)=>window.setData(d)', data)
            page.evaluate('document.fonts.ready')
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            # Check every scene before committing expensive frame rendering.
            for scene in data['scenes']:
                page.evaluate('(t)=>window.renderAt(t)', (scene['start']+scene['end'])/2)
                if page.evaluate('window.lastRender.overflow'):
                    raise RuntimeError('画面文字超出安全排版范围，请先缩短分镜文字。')
            if errors:
                raise RuntimeError('动画脚本错误：'+'; '.join(errors))
            with (out/'render.log').open('w', encoding='utf-8') as log:
                encoder = subprocess.Popen(encode, stdin=subprocess.PIPE, stderr=log)
                try:
                    for i in range(total):
                        jpeg = page.evaluate('(t)=>{window.renderAt(t);return document.getElementById("c").toDataURL("image/jpeg", .96).split(",")[1]}', i/args.fps)
                        encoder.stdin.write(base64.b64decode(jpeg))
                        if i % (args.fps*5) == 0:
                            print(f'渲染 {i/args.fps:.0f}/{args.duration:g} 秒', flush=True)
                    encoder.stdin.close()
                    if encoder.wait() != 0:
                        raise RuntimeError(f'视频编码失败，请查看 {out / "render.log"}')
                    if errors:
                        raise RuntimeError('动画脚本错误：'+'; '.join(errors))
                finally:
                    if encoder.poll() is None:
                        encoder.kill()
                        encoder.wait()
            for name, t in [('cover', 1.8), ('detail', args.duration*.55)]:
                page.evaluate('(t)=>window.renderAt(t)', t)
                page.screenshot(path=str(out/f'{name}.jpg'), type='jpeg', quality=95)
        finally:
            browser.close()
    final = out/'final.mp4'
    fade = min(1.6, args.duration/5)
    af = f'atrim=duration={args.duration},asetpts=N/SR/TB,loudnorm=I=-16:TP=-1.5:LRA=9,afade=t=in:d=0.7,afade=t=out:st={args.duration-fade}:d={fade}'
    mux = [ffmpeg, '-y', '-v', 'error', '-i', str(silent), '-stream_loop', '-1',
           '-ss', str(args.music_start), '-i', str(music)]
    if args.with_voice and not args.no_voice:
        voicefile = out/'voice.mp3'
        asyncio.run(tts(data['narration'], args.voice, voicefile))
        mux += ['-i', str(voicefile), '-filter_complex',
            f'[1:a]{af},volume=0.22[m];[2:a]apad,loudnorm=I=-16:TP=-1.5:LRA=9[v];[m][v]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89[a]']
    else:
        mux += ['-filter_complex', f'[1:a]{af}[a]']
    mux += ['-map', '0:v:0', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
            '-t', str(total/args.fps), '-movflags', '+faststart', str(out/'final.pending.mp4')]
    subprocess.run(mux, check=True)
    report['encoded_output'] = verify_output(ffmpeg, out/'final.pending.mp4', total/args.fps, args.fps)
    (out/'final.pending.mp4').replace(final)
    report.update(render_checks='passed', frames=total, output_file=str(final))
    (out/'quality_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'完成：{final}', flush=True)


if __name__ == '__main__':
    main()
