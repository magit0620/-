"""docx から埋め込みフォントを外してファイルを軽くする（Word 側の「フォントを埋め込む」設定で数MBになるため）。
使い方: python3 strip_fonts.py 入力.docx 出力.docx"""
import sys, re, zipfile
src, dst = sys.argv[1], sys.argv[2]
zin = zipfile.ZipFile(src)
with zipfile.ZipFile(dst + '.tmp', 'w', zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        if item.filename.startswith('word/fonts/'):
            continue
        data = zin.read(item.filename)
        if item.filename == 'word/fontTable.xml':
            data = re.sub(rb'<w:embed(Regular|Bold|Italic|BoldItalic)\b[^>]*/>', b'', data)
        elif item.filename == 'word/_rels/fontTable.xml.rels':
            data = re.sub(rb'<Relationship [^>]*fonts/[^>]*/>', b'', data)
        elif item.filename == 'word/settings.xml':
            data = re.sub(rb'<w:(embedTrueTypeFonts|saveSubsetFonts|embedSystemFonts)\b[^>]*/>', b'', data)
        elif item.filename == '[Content_Types].xml':
            data = re.sub(rb'<Default Extension="odttf"[^>]*/>', b'', data)
        zout.writestr(item, data)
import os; os.replace(dst + '.tmp', dst)
