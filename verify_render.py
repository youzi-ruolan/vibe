import json
from pathlib import Path
import pipeline
from quality import validate_plan, minimum_hold
from playwright.sync_api import sync_playwright
out=Path('output/paper_history');out.mkdir(parents=True,exist_ok=True)
ff=pipeline.find_ffmpeg('ffmpeg.exe');music=pipeline.find_bgm(None)
e,peaks=pipeline.music_analysis(ff,music,42,0)
d=dict(pipeline.CAT['paper_history']);d.update(duration=42,energy=e,scenes=pipeline.storyboard('paper_history',d,42,peaks))
print('Audio peaks',len(peaks),'catalog',len(pipeline.CAT),'history',len(json.loads(Path('topics/history_cases.json').read_text(encoding='utf-8'))))
with sync_playwright() as p:
 b=p.chromium.launch(headless=True);page=b.new_page(viewport={'width':1080,'height':1920});errors=[];page.on('pageerror',lambda exc:errors.append(str(exc)))
 page.goto((Path('public/index.html').resolve()).as_uri());page.evaluate('(d)=>window.setData(d)',d)
 images=[]
 for scene in d['scenes']:
  t=(scene['start']+scene['end'])/2
  page.evaluate('(t)=>renderAt(t)',t)
  assert not page.evaluate('lastRender.overflow'),scene
  images.append(page.evaluate('c.toDataURL("image/jpeg",.88)'))
 for scene in d['scenes'][1:]:
  for t in [scene['start']-.31,scene['start'],scene['start']+.31]:
   page.evaluate('(t)=>renderAt(t)',t);assert page.evaluate('lastRender.mixing')
 continuity=[]
 for scene in d['scenes'][1:]:
  for offset in [-.33,-.01,.31]:
   delta=page.evaluate('''(t)=>{
    const samples=[];
    for(const at of [t,t+1/30]){
      renderAt(at);const pixels=c.getContext('2d').getImageData(0,0,1080,1920).data;
      const a=[];for(let y=0;y<1920;y+=24)for(let x=0;x<1080;x+=24){const i=(y*1080+x)*4;a.push(pixels[i],pixels[i+1],pixels[i+2]);}samples.push(a);
    }
    return samples[0].reduce((sum,v,i)=>sum+Math.abs(v-samples[1][i]),0)/samples[0].length;
   }''',scene['start']+offset)
   continuity.append(delta)
   assert delta<24,('abrupt frame change',scene['start'],offset,delta)
 print('Largest adjacent transition-frame difference:',round(max(continuity),2),'/ 255')
 for key,data in pipeline.CAT.items():
  item=dict(data);item.update(duration=42,scenes=pipeline.storyboard(key,data,42,[]))
  page.evaluate('(d)=>window.setData(d)',item)
  for scene in item['scenes']:
   page.evaluate('(t)=>renderAt(t)',(scene['start']+scene['end'])/2)
   assert not page.evaluate('lastRender.overflow'),key
   assert scene['end']-scene['start']+.001>=minimum_hold(scene),key
  for scene in item['scenes'][1:]:
   for t in [scene['start']-.31,scene['start'],scene['start']+.31]:
    page.evaluate('(t)=>renderAt(t)',t)
    assert page.evaluate('lastRender.mixing'),key
    assert not page.evaluate('lastRender.overflow'),key
  dense=pipeline.storyboard(key,data,42,[i*.05 for i in range(840)])
  assert all(s['end']-s['start']+.001>=minimum_hold(s) for s in dense),key
 try:pipeline.storyboard('paper_history',pipeline.CAT['paper_history'],10,[])
 except ValueError:pass
 else:raise AssertionError('too-short reading duration was accepted')
 assert not errors,errors
 montage=b.new_page(viewport={'width':1080,'height':960},device_scale_factor=1)
 montage.set_content('<body style="margin:0;display:grid;grid-template-columns:repeat(4,270px);background:#17231f">'+''.join('<img style="width:270px;height:480px" src="'+s+'">' for s in images)+'</body>')
 montage.screenshot(path=str(out/'storyboard.jpg'),type='jpeg',quality=94)
 # Inspect an unrelated topic too: diagram labels must belong to its subject.
 steam=dict(pipeline.CAT['steam_history']);steam.update(duration=42,scenes=pipeline.storyboard('steam_history',steam,42,[]))
 page.evaluate('(d)=>window.setData(d)',steam)
 others=[]
 for scene in steam['scenes']:
  page.evaluate('(t)=>renderAt(t)',(scene['start']+scene['end'])/2)
  others.append(page.evaluate('c.toDataURL("image/jpeg",.9)'))
 montage.set_viewport_size({'width':1080,'height':1280})
 montage.set_content('<body style="margin:0;display:grid;grid-template-columns:repeat(3,360px);background:#17231f">'+''.join('<img style="width:360px;height:640px" src="'+s+'">' for s in others)+'</body>')
 montage.screenshot(path=str(out/'pipeline_examples.jpg'),type='jpeg',quality=94)
 b.close()
print(f'PASS: all {len(pipeline.CAT)} curated topics, all scenes and transitions, reading-time limits, dense music alignment; no text overflow or browser errors')
