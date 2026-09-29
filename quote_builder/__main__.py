"""使い方: python -m quote_builder 他社見積.xlsx -o 見積書.xlsx --customer 〇〇株式会社 --subject 件名"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from .pricing import PricingRule, price_items
from .reader import read_competitor_quote
from .writer import QuoteInfo, write_quote


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="quote_builder", description="他社見積を読み込み、自社見積書 (Excel) を作成します")
    ap.add_argument("input", help="他社見積ファイル (.xlsx / .csv / .pdf)")
    ap.add_argument("-o", "--output", help="出力する見積書 (.xlsx)。省略時は 見積書_<入力名>.xlsx")
    ap.add_argument("--customer", default="", help="宛先 (御中の前に入る会社名)")
    ap.add_argument("--subject", default="", help="件名")
    ap.add_argument("--quote-no", default="", help="見積番号 (省略時は日付から自動採番)")
    ap.add_argument("--date", help="発行日 YYYY-MM-DD (省略時は本日)")
    ap.add_argument("--valid-days", type=int, default=30, help="有効期限の日数 (既定 30)")
    ap.add_argument("--rate", type=float, default=0.95, help="他社単価に掛ける率 (既定 0.95 = 5%%安)")
    ap.add_argument("--round", dest="round_unit", type=int, default=10, help="単価の丸め単位 円 (既定 10)")
    ap.add_argument("--round-mode", choices=["down", "up", "nearest"], default="down")
    ap.add_argument("--tax", type=float, default=0.10, help="消費税率 (既定 0.10)")
    ap.add_argument("--company", default="company.json", help="自社情報 JSON (既定 company.json)")
    ap.add_argument("--notes", default="", help="備考")
    ap.add_argument("--no-compare", action="store_true", help="他社比較シートを出力しない")
    args = ap.parse_args(argv)

    try:
        quote = read_competitor_quote(args.input)
    except (ValueError, FileNotFoundError) as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1

    company = {}
    cpath = Path(args.company)
    if cpath.exists():
        company = json.loads(cpath.read_text(encoding="utf-8"))

    issue = date.fromisoformat(args.date) if args.date else date.today()
    info = QuoteInfo(
        customer=args.customer,
        subject=args.subject,
        quote_no=args.quote_no or issue.strftime("Q%Y%m%d-01"),
        issue_date=issue,
        valid_days=args.valid_days,
        tax_rate=args.tax,
        notes=args.notes or company.get("default_notes", ""),
        company=company,
    )
    if company.get("delivery"):
        info.delivery = company["delivery"]
    if company.get("payment"):
        info.payment = company["payment"]

    rule = PricingRule(rate=args.rate, round_unit=args.round_unit, round_mode=args.round_mode)
    priced = price_items(quote.items, rule)
    out = args.output or f"見積書_{Path(args.input).stem}.xlsx"
    write_quote(out, priced, info, vendor=quote.vendor, source=quote.source, compare=not args.no_compare)

    comp = sum(p.competitor_price * p.item.quantity for p in priced)
    ours = sum(p.item.amount for p in priced)
    print(f"読み込み: {quote.source} ({quote.vendor or '他社'}) 明細 {len(priced)} 行")
    for i, p in enumerate(priced, 1):
        print(f"  {i:>2}. {p.item.name}  {p.item.quantity:g}{p.item.unit}  "
              f"¥{p.competitor_price:,.0f} → ¥{p.item.unit_price:,.0f}")
    print(f"他社合計(税抜) ¥{comp:,.0f} / 自社合計(税抜) ¥{ours:,.0f} (差額 ¥{ours - comp:,.0f})")
    print(f"出力: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
