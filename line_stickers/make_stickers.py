"""スタンプシート画像を切り出して LINE スタンプ用の透過PNGを作る。

使い方: python3 make_stickers.py <シート画像> <出力先> 列数 行数 [下端を閉じる番号,...]
  体の下側に輪郭線がない絵（半身で切れている絵）は番号を指定すると下端を閉じて白を残す。
"""
import os, sys
from PIL import Image
import numpy as np
from scipy import ndimage as ndi

W, H, M = 370, 320, 10  # LINE スタンプ最大サイズと余白
GAP = 5  # 塞ぐ輪郭線の途切れの幅(px)

def boundaries(proj, n):
    # 等分位置の付近で前景が最も少ない位置を区切りにする
    L = len(proj); cuts = [0]
    for k in range(1, n):
        c = L * k // n; w = L // (2 * n)
        cuts.append(c - w + int(np.argmin(proj[c - w:c + w])))
    return cuts + [L]

def fit(img, w, h, m):
    s = min((w - 2 * m) / img.width, (h - 2 * m) / img.height)
    t = img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)
    cv = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    cv.paste(t, ((w - t.width) // 2, (h - t.height) // 2), t)
    return cv

def main(src, out, ncol, nrow, close_bottom=()):
    a = np.asarray(Image.open(src).convert('RGB')).astype(int)
    mn = a.min(2)
    # 外周とつながった白を背景とみなす（キャラ内部の白は残す）
    # 輪郭線の小さな途切れから背景が中へ漏れないよう、線を太らせて塞いでから判定する
    light = mn >= 225
    wall = ndi.binary_dilation(~light, iterations=GAP)
    fgm0 = ~light
    xs_cut = boundaries(fgm0.sum(0), ncol)
    ys_cut = boundaries(fgm0.sum(1), nrow)
    for k in close_bottom:
        # 指定セルの最下部の線の左右端を水平の壁でつなぐ
        r, c = divmod(k - 1, ncol)
        y0, y1, x0, x1 = ys_cut[r], ys_cut[r + 1], xs_cut[c], xs_cut[c + 1]
        cell = fgm0[y0:y1, x0:x1]
        yb = np.where(cell.any(1))[0].max()
        band = cell[max(0, yb - 15):yb + 1]
        xb = np.where(band.any(0))[0]
        wall[y0 + yb - GAP:y0 + yb + 1, x0 + xb.min():x0 + xb.max() + 1] = True
    lab, _ = ndi.label(light & ~wall)
    edge = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    bg = np.isin(lab, list(edge))
    # 太らせた分だけ背景を明るい画素へ広げ直す
    bg = ndi.binary_dilation(bg, iterations=GAP + 1, mask=light)
    fgm = ~bg
    # 前景の連結成分を重心のあるセルに割り当てる
    comp, n = ndi.label(fgm)
    idx = range(1, n + 1)
    sizes = ndi.sum(fgm, comp, idx)
    cents = ndi.center_of_mass(fgm, comp, idx)
    cellmap = np.zeros(n + 1, int) - 1
    for i, (s, (cy, cx)) in enumerate(zip(sizes, cents), 1):
        if s < 15:
            continue
        r = np.searchsorted(ys_cut, cy, 'right') - 1
        c = np.searchsorted(xs_cut, cx, 'right') - 1
        cellmap[i] = r * ncol + c
    cellid = cellmap[comp]
    os.makedirs(out, exist_ok=True)
    cells = []
    for k in range(ncol * nrow):
        m = cellid == k
        ring = ndi.binary_dilation(m) & ~m & ~fgm
        alpha = m.astype(float)
        alpha[ring] = np.clip((255 - mn[ring]) / 255 * 4, 0, 1)  # 縁のなじませ
        ys, xs = np.where(alpha > 0)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        rgba = np.dstack([a[y0:y1, x0:x1], alpha[y0:y1, x0:x1] * 255]).astype(np.uint8)
        cells.append(Image.fromarray(rgba, 'RGBA'))
    for i, c in enumerate(cells, 1):
        fit(c, W, H, M).save(f'{out}/{i:02d}.png', optimize=True)
    fit(cells[0], 240, 240, 10).save(f'{out}/main.png', optimize=True)
    fit(cells[0], 96, 74, 2).save(f'{out}/tab.png', optimize=True)
    pv = Image.new('RGBA', (W * ncol, H * nrow), (60, 60, 70, 255))
    for i, c in enumerate(cells):
        t = fit(c, W, H, M); pv.paste(t, ((i % ncol) * W, (i // ncol) * H), t)
    pv.convert('RGB').save(f'{out}/preview.png')

if __name__ == '__main__':
    cb = [int(x) for x in sys.argv[5].split(',')] if len(sys.argv) > 5 else []
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), cb)
