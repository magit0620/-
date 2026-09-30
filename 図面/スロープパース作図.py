import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Polygon, Patch
font_manager.fontManager.addfont("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc")
plt.rcParams["font.family"]="WenQuanYi Zen Hei"; plt.rcParams["axes.unicode_minus"]=False
import logging; logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

W=1580.0; Y1,Y2,Y3,Y4=1424.,2624.,4470.,8770.
P3=(W,Y1,71.); P2=(0,Y2,12.); P1=(W,Y3,119.)
def bary(p,a,b,c):
    (x,y)=p; x1,y1,_=a;x2,y2,_=b;x3,y3,_=c
    d=(y2-y3)*(x1-x3)+(x3-x2)*(y1-y3)
    l1=((y2-y3)*(x-x3)+(x3-x2)*(y-y3))/d; l2=((y3-y1)*(x-x3)+(x1-x3)*(y-y3))/d
    return l1,l2,1-l1-l2
def tri(p,a,b,c):
    l=bary(p,a,b,c); return l[0]*a[2]+l[1]*b[2]+l[2]*c[2], min(l)
def bil(X,Y,ya,yb,z00,z10,z01,z11):
    u=X/W; v=(Y-ya)/(yb-ya)
    return z00*(1-u)*(1-v)+z10*u*(1-v)+z01*(1-u)*v+z11*u*v
S_tris=[(P3,(0,Y1,17.),(0,945.,19.)),(P3,(0,945.,19.),(0,0,24.)),(P3,(0,0,24.),(W,0,24.))]
N_tris=[(P2,(W,Y2,71.),P1),(P2,P1,(0,Y3,124.))]
def h(X,Y):
    if Y<=Y1:
        best=max((tri((X,Y),*t) for t in S_tris),key=lambda r:r[1]); return best[0]
    if Y<=Y2: return bil(X,Y,Y1,Y2,17,71,12,71)
    if Y<=Y3:
        best=max((tri((X,Y),*t) for t in N_tris),key=lambda r:r[1]); return best[0]
    return bil(X,Y,Y3,Y4,124,119,404,402)

E=3.0  # vertical exaggeration of floor
C=np.array([790.,-4300.,3100.]); T=np.array([790.,4300.,-200.])
f=T-C; f/=np.linalg.norm(f); r=np.cross(f,[0,0,1.]); r/=np.linalg.norm(r); u=np.cross(r,f)
def pr(P):
    d=np.asarray(P,float)-C; z=d@f
    return np.array([d@r/z, d@u/z]), z
fig=plt.figure(figsize=(16.54,11.69))
ax=fig.add_axes([0.02,0.30,0.70,0.66]); ax.set_aspect("equal"); ax.axis("off")
cls=[(0,2,"#8fd18f","2%未満"),(2,3,"#d9ec7a","2〜3%"),(3,4,"#ffd966","3〜4%"),(4,5,"#f6a95b","4〜5%"),(5,99,"#e8665a","5%以上")]
def col(s):
    for a,b,c,_ in cls:
        if a<=s<b: return c
polys=[]
nx=48; ys=np.concatenate([np.linspace(0,Y1,15),np.linspace(Y1,Y2,13)[1:],np.linspace(Y2,Y3,61)[1:],np.linspace(Y3,Y4,22)[1:]])
xs=np.linspace(0,W,nx+1)
H=np.array([[h(x,y) for x in xs] for y in ys])
for j in range(len(ys)-1):
    for i in range(nx):
        x0,x1_,y0,y1_=xs[i],xs[i+1],ys[j],ys[j+1]
        xc,yc=(x0+x1_)/2,(y0+y1_)/2; e=5
        gx=(h(xc+e,yc)-h(xc-e,yc))/(2*e); gy=(h(xc,yc+e)-h(xc,yc-e))/(2*e)
        s=100*np.hypot(gx,gy)
        pts=[(x0,y0,H[j,i]),(x1_,y0,H[j,i+1]),(x1_,y1_,H[j+1,i+1]),(x0,y1_,H[j+1,i])]
        P=[pr((a,b,c*E)) for a,b,c in pts]
        polys.append((np.mean([p[1] for p in P]),[p[0] for p in P],col(s)))
# exterior stone outside door (+71)
for d,pp,c in sorted(polys,key=lambda t:-t[0]):
    ax.add_patch(Polygon(pp,closed=True,fc=c,ec=c,lw=0.3))
# contour lines every 10mm
cs=plt.figure().add_subplot().contour(xs,ys,H,levels=np.arange(20,410,10))
for lev,segs in zip(cs.levels,cs.allsegs):
    for sg in segs:
        P=np.array([pr((x,y,h(x,y)*E))[0] for x,y in sg])
        ax.plot(P[:,0],P[:,1],color="#555",lw=0.35 if lev%50 else 0.8,alpha=0.7)
plt.close(2)
# grid edges of regions (boundaries)
def edge3(a,b,n=30,**kw):
    pts=[(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t) for t in np.linspace(0,1,n)]
    P=np.array([pr((x,y,h(min(max(x,0),W),y)*E))[0] for x,y in pts]); ax.plot(P[:,0],P[:,1],**kw)
for yb in (Y1,Y2,Y3): edge3((0,yb),(W,yb),color="#1f4fbf",lw=1.0,ls="--")
edge3((0,Y2),(W,Y3),color="#1f4fbf",lw=0.8,ls=":")
edge3((0,0),(W,0),color="k",lw=1)
# walls (base follows floor edge, height 2400 true)
WH=2400
def wall(X,ya,yb,alpha,fc):
    ysw=np.linspace(ya,yb,40)
    bot=[pr((X,y,h(min(X,W),y)*E))[0] for y in ysw]; top=[pr((X,y,h(min(X,W),y)*E+WH))[0] for y in ysw]
    ax.add_patch(Polygon(bot+top[::-1],closed=True,fc=fc,ec="#666",lw=0.8,alpha=alpha))
wall(0,0,Y4,0.18,"#b0a898")
wall(W,Y3,Y4,0.18,"#b0a898")
# right wall at door zone: FIX + door (glass)
fr0,fr1=Y1-1170,Y2+1170
wall(W,0,fr0,0.25,"#b0a898"); wall(W,fr1,Y3,0.25,"#b0a898")
def rect_on_right(ya,yb,za,zb,**kw):
    pts=[(W,ya,za),(W,yb,za),(W,yb,zb),(W,ya,zb)]
    P=[pr(p)[0] for p in pts]; ax.add_patch(Polygon(P,closed=True,**kw))
z71=71*E
rect_on_right(fr0,fr1,z71,z71+1965,fc="none",ec="#1f4fbf",lw=1.6)
rect_on_right(fr0,Y1,z71,z71+1965,fc="#a9d3f5",ec="#1f4fbf",lw=0.8,alpha=0.35)
rect_on_right(Y2,fr1,z71,z71+1965,fc="#a9d3f5",ec="#1f4fbf",lw=0.8,alpha=0.35)
rect_on_right(Y1,Y2,z71,z71+1965,fc="#e8f4ff",ec="#1f4fbf",lw=1.2,alpha=0.25)
rect_on_right(fr0,fr1,z71+1965,2400+z71,fc="#9aa7b8",ec="#1f4fbf",lw=0.8,alpha=0.5)
def lab(X,Y,s,dz=0,dx=0,dy=0,c="#0b2a8a",fs=12,bold=True,**kw):
    p=pr((X,Y,h(min(max(X,0),W),Y)*E+dz))[0]
    ax.text(p[0]+dx,p[1]+dy,s,color=c,fontsize=fs,ha="center",va="center",fontweight="bold" if bold else None,
            bbox=dict(boxstyle="round,pad=0.2",fc="white",ec="none",alpha=0.8),**kw)
def dot(X,Y):
    p=pr((X,Y,h(X,Y)*E))[0]; ax.plot(*p,"o",color="#0b2a8a",ms=4)
for X,Y,s in [(0,0,"+24"),(W,0,"+24"),(0,945,"+19"),(0,Y1,"+17"),(W,Y1,"+71"),(0,Y2,"+12"),(W,Y2,"+71"),(0,Y3,"+124"),(W,Y3,"+119"),(0,Y4,"+404"),(W,Y4,"+402")]:
    dot(X,Y); lab(X+(180 if X==0 else -180),Y,s,dz=0,fs=11 if Y<Y4 else 10)
def arrow(a,b,s,off=(0,0)):
    pa=pr((a[0],a[1],h(*a)*E+15))[0]; pb=pr((b[0],b[1],h(*b)*E+15))[0]
    ax.annotate("",xy=pb,xytext=pa,arrowprops=dict(arrowstyle="-|>",color="#c0392b",lw=1.8,mutation_scale=14))
    m=(pa+pb)/2; ax.text(m[0]+off[0],m[1]+off[1],s,color="#c0392b",fontsize=13,fontweight="bold",ha="center",va="center",
        bbox=dict(boxstyle="round,pad=0.2",fc="white",ec="#c0392b",lw=0.8))
# arrows point downhill
arrow((W-80,2000),(80,2000),"3.3〜3.7%",off=(0,0.012))
arrow((W-60,Y1-60),(W-60,250),"3.3%",off=(0.03,0))
arrow((W-120,Y1-100),(150,300),"2.2〜3.2%",off=(0,-0.012))
arrow((W-80,Y3-150),(W-80,Y2+150),"2.6%",off=(0.028,0))
arrow((80,Y3-150),(80,Y2+150),"6.1%",off=(-0.028,0))
arrow((790,Y4-400),(790,Y3+300),"6.49%（既存）",off=(0.035,0))
lab(W,(Y1+Y2)/2,"自動ドア W1200\n敷居 +71",dz=1100,dx=0.02,c="#1f4fbf",fs=11)
lab(790,700,"視点：東端（+24付近）",dz=0,dy=-0.03,c="#333",fs=10,bold=False)
lab(0,6700,"南側 壁",dz=1300,dx=0.02,c="#555",fs=10,bold=False)
lab(W,6700,"北側 壁",dz=1300,dx=-0.02,c="#555",fs=10,bold=False)
ax.autoscale_view(); ax.margins(0.02)
ax.set_title("本願寺様 嘉枝堂渡り廊下　スロープ部パース（東から西を見る）",fontsize=18,fontweight="bold",loc="left")
# legend / notes
ax2=fig.add_axes([0.73,0.30,0.26,0.62]); ax2.axis("off")
ax2.legend(handles=[Patch(fc=c,ec="#666",label=l) for _,_,c,l in cls],title="床の勾配（色分け）",loc="upper left",fontsize=12,title_fontsize=13,frameon=True)
notes=["・数字は計画高さ（mm、±0基準）","・赤矢印は下り方向と勾配","・細線は高さ10mmごとの等高線","・扉前（ドア幅部分）は幅方向に","  扉側+71 → 南壁側+12〜+17","  （3.3〜3.7%）の片流れ","・6.1%（南壁側の縦断）は計画高さ","  +12→+124 から算出した値","","※高さ方向を3倍に強調して表示","※計画平面図（2026/09/15）より作成","  した概略パースです"]
for i,s in enumerate(notes): ax2.text(0.02,0.58-i*0.05,s,fontsize=12,transform=ax2.transAxes)
# profile
ax3=fig.add_axes([0.06,0.05,0.90,0.20])
R=[(0,24),(Y1,71),(Y2,71),(Y3,119),(Y4,402)]; L=[(0,24),(945,19),(Y1,17),(Y2,12),(Y3,124),(Y4,404)]
ax3.plot(*zip(*R),"-o",color="#1f4fbf",lw=2,ms=4,label="北側（扉側）縦断")
ax3.plot(*zip(*L),"-o",color="#8a6d3b",lw=2,ms=4,label="南側（壁側）縦断")
for pts,c,dy in [(R,"#1f4fbf",14),(L,"#8a6d3b",-22)]:
    for (a,za),(b,zb) in zip(pts,pts[1:]):
        s=abs(zb-za)/(b-a)*100
        ax3.text((a+b)/2,(za+zb)/2+dy,f"{s:.1f}%",color=c,fontsize=10,ha="center")
    for a,z in pts: ax3.text(a,z+(dy*0.6 if dy>0 else dy*0.6)-4,f"+{z}",color=c,fontsize=8,ha="center")
ax3.axvspan(Y1,Y2,color="#a9d3f5",alpha=0.4); ax3.text((Y1+Y2)/2,370,"自動ドア\nW1200",ha="center",fontsize=10,color="#1f4fbf")
ax3.set_xlim(-200,Y4+200); ax3.set_ylim(-40,440)
ax3.set_xlabel("東端からの距離（mm） 東 → 西",fontsize=11); ax3.set_ylabel("計画高さ(mm)",fontsize=11)
ax3.grid(alpha=0.3); ax3.legend(loc="upper left",fontsize=10)
ax3.set_title("縦断図（高さ方向を約10倍に強調）",fontsize=12,loc="left")
out="/home/user/-/図面/本願寺_スロープ部パース_東から西.png"
fig.savefig(out,dpi=130); fig.savefig(out.replace(".png",".pdf")); print("ok")
