from PIL import Image
import numpy as np, os
from scipy import ndimage as ndi
src=Image.open('../images/1.webp').convert('RGB')
im=np.asarray(src).astype(int)
cx=[48,279,309,516,536,749,772,1002,1021,1234]
cols=[(0,294),(294,526),(526,760),(760,1011),(1011,1264)]
rows=[(0,288),(288,556),(556,843)]
out='/home/user/-/line_stickers'; os.makedirs(out,exist_ok=True)
W,H,M=370,320,10
cells=[]
for r in rows:
    for c in cols:
        a=im[r[0]:r[1],c[0]:c[1]]
        mn=a.min(2)
        light=mn>=225
        lab,n=ndi.label(light)
        border=set(np.unique(np.r_[lab[0],lab[-1],lab[:,0],lab[:,-1]]))-{0}
        bg=np.isin(lab,list(border))
        fgm=~bg
        # drop tiny specks
        l2,n2=ndi.label(fgm); sz=ndi.sum(fgm,l2,range(1,n2+1))
        fgm=np.isin(l2,[i+1 for i,s in enumerate(sz) if s>=15])
        # soft alpha at edge: pixels in bg adjacent to fg get alpha from darkness
        ring=ndi.binary_dilation(fgm)&~fgm
        alpha=fgm.astype(float)
        dark=(255-mn)/255.0
        alpha[ring]=np.clip(dark[ring]*4,0,1)
        rgba=np.dstack([a,(alpha*255)]).astype(np.uint8)
        ys,xs=np.where(alpha>0)
        rgba=rgba[ys.min():ys.max()+1,xs.min():xs.max()+1]
        cells.append(Image.fromarray(rgba,'RGBA'))
def fit(img,w,h,m):
    s=min((w-2*m)/img.width,(h-2*m)/img.height)
    t=img.resize((max(1,round(img.width*s)),max(1,round(img.height*s))),Image.LANCZOS)
    cv=Image.new('RGBA',(w,h),(0,0,0,0))
    cv.paste(t,((w-t.width)//2,(h-t.height)//2),t); return cv
for i,c in enumerate(cells,1):
    fit(c,W,H,M).save(f'{out}/{i:02d}.png',optimize=True)
fit(cells[0],240,240,10).save(f'{out}/main.png',optimize=True)
fit(cells[0],96,74,2).save(f'{out}/tab.png',optimize=True)
# preview on dark + checker
pv=Image.new('RGBA',(W*5,H*3),(60,60,70,255))
for i,c in enumerate(cells):
    t=fit(c,W,H,M); pv.paste(t,((i%5)*W,(i//5)*H),t)
pv.convert('RGB').save('preview_dark.png')
print([c.size for c in cells])
