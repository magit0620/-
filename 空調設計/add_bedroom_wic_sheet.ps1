# 「夏夜　個別　寝室・WIC」シートを追加して入力値を入れる
# Excel の COM を使うので、図・書式・数式はそのまま残る。
# 実行前にバックアップを同じフォルダに作る。Excel でファイルを閉じてから実行すること。
$ErrorActionPreference = 'Stop'

$path    = 'C:\Users\nagat\Desktop\進行中\空調講座資料\発表用資料　モデル\発表用　空調設計シート　モデルハウス.xlsx'
$srcName = '夏夜　個別　防音室 (2)'     # 書式のひな形（同じ設計点・夏の夜）
$newName = '夏夜　個別　寝室・WIC'

if (-not (Test-Path -LiteralPath $path)) { throw "ファイルが見つかりません: $path" }

# Excel で開いたままだと保存できないので先に確かめる
try { $fs = [System.IO.File]::Open($path, 'Open', 'ReadWrite', 'None'); $fs.Close() }
catch { throw 'ファイルが Excel で開かれています。閉じてからもう一度実行してください。' }

$bak = $path -replace '\.xlsx$', ('_バックアップ_' + (Get-Date -Format 'yyyyMMdd_HHmm') + '.xlsx')
Copy-Item -LiteralPath $path -Destination $bak
Write-Host "バックアップ: $bak"

$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
try {
    $wb = $xl.Workbooks.Open($path)
    foreach ($s in $wb.Worksheets) {
        if ($s.Name -eq $newName) { throw "シート「$newName」はもうあります。消してから実行してください。" }
    }
    $src = $wb.Worksheets.Item($srcName)
    $src.Copy([System.Reflection.Missing]::Value, $src)
    $ws = $wb.Worksheets.Item($src.Index + 1)
    $ws.Name = $newName

    # ひな形（防音室）の入力値を消す。数式のセルは残す
    function Clear-Constants($addr) {
        foreach ($c in $ws.Range($addr).Cells) {
            if (-not $c.HasFormula -and $null -ne $c.Value2) { [void]$c.ClearContents() }
        }
    }
    Clear-Constants 'B10:C19'   # 常時電力・PC・TV・照明・再熱など
    Clear-Constants 'B23:C26'   # 日射
    Clear-Constants 'H10:I16'   # 潜熱の機器
    Clear-Constants 'A34:M70'   # 防音室のメモ

    $vals = [ordered]@{
        'C1'  = '夏'; 'G1' = '寝室・WIC'; 'K1' = '夜'
        'C3'  = 26      # 隣室温度（階段・吹抜け＝全館の設定室温）
        'C4'  = 26      # 室温（全館の設定室温）
        'E4'  = 55      # 室内湿度（第3回p17 ストライクゾーン内）
        'I4'  = 28.2    # 外気 2023/8/14 23:00
        'K4'  = 89
        'C5'  = 0       # 外気の直接導入なし（ダクト給気に含まれ全館シートで計上済み）
        'C7'  = 0
        'I7'  = 0
        'B9'  = 60      # 人体 顕熱（就寝）
        'C9'  = 2       # 2人
        'H9'  = 30      # 人体 潜熱（就寝）
        'C29' = 42.45   # 外皮面積 主寝室23.83＋WIC18.62
        'C30' = 0.2905  # UA値 12.33W/K ÷ 42.45㎡
        'Q11' = 0       # AC欄は使わない
    }
    foreach ($k in $vals.Keys) { $ws.Range($k).Value2 = $vals[$k] }
    foreach ($k in @('B20', 'B21')) {     # 暖冷気流入・間仕切り（隣も26℃で温度差0）
        if (-not $ws.Range($k).HasFormula) { $ws.Range($k).Value2 = 0 }
    }

    $memo = @(
        '主寝室＋WIC を1ゾーンとして負荷を出す（室温26℃固定）。',
        '隣室（階段・吹抜け）も全館の26℃なので、暖冷気流入・間仕切りは温度差0。',
        'C5=0：この部屋に外気の直接導入はない。換気分はダクト給気に含まれ、全館シートで計上済み。',
        'B9/H9：就寝時 顕熱60W・潜熱30W × 2人。照明0（就寝中）、日射0（23時）。',
        '外気：2023/8/14 23:00　28.2℃89%（絶対湿度21.6g/kg・5年43,824時刻中1位）。防音室と同じ設計点。',
        'C29=42.45㎡：主寝室23.83（W10込み）＋WIC18.62',
        'C30=0.2905：熱損失 主寝室8.27＋WIC4.06＝12.33W/K ÷ 42.45㎡',
        '　WIC：外壁(1.82+2.73)×3.0＝13.65㎡×0.189＝2.58　床4.97㎡×0.426×0.7＝1.48　天井0（上は2階）窓なし',
        'ダクト2本：452.39㎥/h÷吹出口9×2＝100.5㎥/h（均等配分と仮定）',
        '取れる熱 0.34×100.5×(26−16.0)＝342W ＞ 必要 D33≒207W',
        '→ 必要風量 207÷(0.34×10)＝60.9㎥/h。割当は1.7倍過剰。絞って玄関（16%不足）へ回す。',
        '※吹出16.0℃は仮定（全館の夏夜シートは未作成）'
    )
    for ($i = 0; $i -lt $memo.Count; $i++) { $ws.Cells.Item(36 + $i, 2).Value2 = $memo[$i] }

    $xl.CalculateFull()
    Write-Host ''
    Write-Host "シート「$newName」を作成しました"
    foreach ($r in @(@('E9','人体顕熱',120), @('E31','外皮',27), @('B32','顕熱合計',147), @('H32','潜熱合計',60), @('D33','合計負荷',207), @('K33','負荷顕熱比',0.710))) {
        $v = $ws.Range($r[0]).Value2
        Write-Host ('  {0,-4} {1,-8} = {2,10:N3}   (予想 {3})' -f $r[0], $r[1], $v, $r[2])
    }
    $wb.Save()
    $wb.Close($false)
    Write-Host ''
    Write-Host '保存しました。'
}
finally {
    $xl.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl)
}
