#!/usr/bin/env python3
"""
영수증 스캐너 CLI
- 카메라로 바로 촬영하거나 갤러리(파일)에서 선택해 분석합니다.
- 분석 결과를 터미널에 출력하고 JSON 파일로 저장합니다.

사용법:
    python cli.py                  # 대화형 메뉴
    python cli.py --file image.jpg # 파일 직접 지정
    python cli.py --camera         # 카메라 바로 실행
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def capture_from_camera() -> bytes:
    """웹캠으로 영수증 촬영"""
    try:
        import cv2
    except ImportError:
        print("❌ 카메라 기능을 사용하려면 opencv-python을 설치하세요:")
        print("   pip install opencv-python")
        sys.exit(1)

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Windows DirectShow 사용
    if not cap.isOpened():
        # DirectShow 실패 시 기본 백엔드로 재시도
        cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ 카메라를 열 수 없습니다. 카메라가 연결되어 있는지 확인하세요.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("\n📷 카메라가 켜졌습니다.")
    print("  [SPACE] 촬영  |  [Q] 취소\n")

    # 창을 반드시 앞으로 띄우기
    cv2.namedWindow("Receipt Scanner", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Receipt Scanner", 960, 540)

    frame_bytes = None
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ 카메라에서 프레임을 읽을 수 없습니다.")
            break

        # 영수증 촬영 가이드라인 오버레이
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (w // 6, h // 8), (w * 5 // 6, h * 7 // 8), (0, 255, 100), 2)
        cv2.putText(frame, "Receipt Area", (w // 6, h // 8 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 100), 2)
        cv2.putText(frame, "SPACE: Capture  Q: Quit", (10, h - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow("Receipt Scanner", frame)
        cv2.setWindowProperty("Receipt Scanner", cv2.WND_PROP_TOPMOST, 1)  # 항상 위에

        key = cv2.waitKey(30) & 0xFF  # 1ms → 30ms로 안정화
        if key == ord("q") or key == 27:  # Q 또는 ESC
            print("촬영을 취소했습니다.")
            cap.release()
            cv2.destroyAllWindows()
            sys.exit(0)
        elif key == ord(" "):
            _, buf = cv2.imencode(".jpg", frame)
            frame_bytes = buf.tobytes()
            print("✅ 촬영 완료!")
            break

    cap.release()
    cv2.destroyAllWindows()
    return frame_bytes


def load_from_file(path: str) -> tuple[bytes, str]:
    """파일에서 이미지 로드"""
    p = Path(path)
    if not p.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {path}")
        sys.exit(1)

    suffix = p.suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
        ".heic": "image/heic", ".heif": "image/heif",
    }
    media_type = mime_map.get(suffix)
    if not media_type:
        print(f"❌ 지원하지 않는 파일 형식: {suffix}")
        sys.exit(1)

    return p.read_bytes(), media_type


def print_result(result: dict):
    """분석 결과를 태그 그룹별로 터미널에 출력"""
    print(f"\n{'━' * 48}")
    print("  🧾  영수증 분석 결과")
    print(f"{'━' * 48}")

    def row(label, value, color="\033[0m"):
        if value:
            print(f"  {color}{label:<10}\033[0m {value}")

    row("업체명", result.get("업체명"), "\033[96m")
    date = result.get("날짜", "")
    time_ = result.get("시간", "")
    row("방문일시", f"{date} {time_}".strip(), "\033[93m")
    row("주소", result.get("주소"))
    row("결제방법", result.get("결제방법"))

    # 태그 그룹별 출력
    tag_groups = result.get("태그그룹", [])
    if tag_groups:
        print()
        for group in tag_groups:
            emoji = group.get("이모지", "📦")
            tag = group.get("태그", "")
            subtotal = group.get("소계", 0)
            items = group.get("항목들", [])

            # 태그 헤더
            print(f"  {emoji} \033[95m{tag}\033[0m  (소계: \033[93m{subtotal:,}원\033[0m)")
            print(f"  {'─' * 44}")

            for item in items:
                name = item.get("항목", "")
                qty = item.get("수량", 1)
                amount = item.get("금액")
                qty_str = f" ×{qty}" if qty and qty > 1 else ""
                amt_str = f"{amount:,}원" if amount else ""
                print(f"    · {name}{qty_str:<22} {amt_str:>10}")
            print()
    else:
        # 태그 없을 때 fallback: 기존 방식
        items = result.get("이용내역", [])
        if items:
            print(f"\n  {'이용 내역':─<42}")
            for item in items:
                name = item.get("항목", "")
                qty = item.get("수량", 1)
                amount = item.get("금액")
                qty_str = f" ×{qty}" if qty and qty > 1 else ""
                amt_str = f"{amount:,}원" if amount else ""
                print(f"  · {name}{qty_str:<25} {amt_str:>10}")

    print(f"  {'─' * 44}")
    if result.get("할인금액"):
        print(f"  {'할인':<10} -\033[91m{result['할인금액']:,}원\033[0m")
    if result.get("부가세"):
        print(f"  {'부가세':<10} {result['부가세']:,}원")
    total = result.get("총금액")
    if total:
        print(f"  \033[92m{'총 결제액':<10} {total:,}원\033[0m")
    print(f"{'━' * 48}\n")


def save_result(result: dict, image_path: str = "camera"):
    """결과를 JSON 파일로 저장"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = Path(image_path).stem if image_path != "camera" else "camera"
    out_path = Path(f"receipt_{stem}_{timestamp}.json")
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"💾 결과 저장: {out_path}")


def analyze_image(image_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    """ReceiptService를 직접 호출 (동기 래퍼)"""
    import asyncio

    # 로컬 import (같은 폴더에 receipt_service.py 필요)
    try:
        from receipt_service import ReceiptService
    except ImportError:
        print("❌ receipt_service.py 파일이 같은 폴더에 있어야 합니다.")
        sys.exit(1)

    service = ReceiptService()

    result = asyncio.run(service.analyze(image_bytes, media_type))
    return result.model_dump()


def interactive_menu() -> tuple[bytes, str, str]:
    """대화형 소스 선택 메뉴"""
    print("\n┌─────────────────────────────┐")
    print("│    🧾  영수증 AI 스캐너      │")
    print("├─────────────────────────────┤")
    print("│  1. 📷  카메라로 촬영        │")
    print("│  2. 🖼   파일에서 선택        │")
    print("│  3. 🚪  종료                 │")
    print("└─────────────────────────────┘")

    choice = input("선택 (1/2/3): ").strip()

    if choice == "1":
        image_bytes = capture_from_camera()
        return image_bytes, "image/jpeg", "camera"
    elif choice == "2":
        path = input("이미지 파일 경로: ").strip().strip('"')
        image_bytes, media_type = load_from_file(path)
        return image_bytes, media_type, path
    else:
        print("종료합니다.")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="영수증 AI 스캐너 CLI")
    parser.add_argument("--file", "-f", help="분석할 이미지 파일 경로")
    parser.add_argument("--camera", "-c", action="store_true", help="카메라로 바로 촬영")
    parser.add_argument("--no-save", action="store_true", help="JSON 파일 저장 안 함")
    args = parser.parse_args()

    if args.camera:
        image_bytes = capture_from_camera()
        media_type, src = "image/jpeg", "camera"
    elif args.file:
        image_bytes, media_type = load_from_file(args.file)
        src = args.file
    else:
        image_bytes, media_type, src = interactive_menu()

    print("\n🔍 AI가 영수증을 분석 중입니다...")
    result = analyze_image(image_bytes, media_type)

    print_result(result)

    if not args.no_save:
        save_result(result, src)


if __name__ == "__main__":
    main()
