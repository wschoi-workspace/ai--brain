#!/usr/bin/env python3
"""
Receipt OCR GUI - Tkinter 기반 폴더 선택 + 진행률 표시 앱
"""

import os
import sys
import threading
import subprocess
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# 같은 폴더의 모듈 import
sys.path.insert(0, str(Path(__file__).resolve().parent))
from receipt_ocr import process_folder, scan_folder, check_api_key, SUPPORTED_EXTS
from excel_writer import write_excel, generate_output_filename


class ReceiptOCRApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("영수증 OCR → Excel 변환기")
        self.root.geometry("680x520")

        self.folder_path: Path | None = None
        self.output_path: Path | None = None
        self.is_running = False

        self._build_ui()

        if not check_api_key():
            messagebox.showerror(
                "API 키 없음",
                "GEMINI_API_KEY가 .env 파일에 설정되어 있지 않습니다.\n"
                ".env 파일을 확인해주세요."
            )

    def _build_ui(self):
        # Main padding
        main = ttk.Frame(self.root, padding=15)
        main.pack(fill="both", expand=True)

        # 제목
        title = ttk.Label(
            main, text="영수증 OCR → Excel 변환기",
            font=("Helvetica", 16, "bold")
        )
        title.pack(pady=(0, 15))

        # 폴더 선택 프레임
        folder_frame = ttk.Frame(main)
        folder_frame.pack(fill="x", pady=5)

        ttk.Label(folder_frame, text="영수증 폴더:").pack(side="left")
        self.folder_var = tk.StringVar(value="(폴더를 선택하세요)")
        self.folder_label = ttk.Label(
            folder_frame, textvariable=self.folder_var,
            relief="sunken", padding=5, width=50
        )
        self.folder_label.pack(side="left", padx=5, fill="x", expand=True)

        self.browse_btn = ttk.Button(
            folder_frame, text="찾아보기", command=self._on_browse
        )
        self.browse_btn.pack(side="left")

        # 파일 개수 표시
        self.count_var = tk.StringVar(value="")
        count_label = ttk.Label(main, textvariable=self.count_var, foreground="gray")
        count_label.pack(pady=(3, 10))

        # 변환 시작 버튼
        self.start_btn = ttk.Button(
            main, text="변환 시작", command=self._on_start, state="disabled"
        )
        self.start_btn.pack(pady=5)

        # 진행률
        progress_frame = ttk.Frame(main)
        progress_frame.pack(fill="x", pady=10)

        self.progress = ttk.Progressbar(
            progress_frame, mode="determinate", length=500
        )
        self.progress.pack(side="left", fill="x", expand=True)

        self.progress_var = tk.StringVar(value="0 / 0")
        ttk.Label(
            progress_frame, textvariable=self.progress_var, width=10
        ).pack(side="left", padx=5)

        # 로그 영역
        ttk.Label(main, text="로그:").pack(anchor="w", pady=(10, 3))
        log_frame = ttk.Frame(main)
        log_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(log_frame, height=12, wrap="none", font=("Menlo", 10))
        log_scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")

        # 결과 열기 버튼
        self.open_btn = ttk.Button(
            main, text="결과 Excel 열기", command=self._on_open_result, state="disabled"
        )
        self.open_btn.pack(pady=(10, 0))

    def _on_browse(self):
        folder = filedialog.askdirectory(title="영수증 이미지 폴더 선택")
        if not folder:
            return

        self.folder_path = Path(folder)
        self.folder_var.set(str(self.folder_path))

        images = scan_folder(self.folder_path)
        exts_str = ", ".join(sorted(SUPPORTED_EXTS))
        self.count_var.set(f"이미지 파일 {len(images)}개 발견 ({exts_str})")

        if len(images) > 0:
            self.start_btn.config(state="normal")
        else:
            self.start_btn.config(state="disabled")
            messagebox.showwarning(
                "이미지 없음",
                f"선택한 폴더에 지원되는 이미지 파일이 없습니다.\n지원 포맷: {exts_str}"
            )

    def _on_start(self):
        if self.is_running or not self.folder_path:
            return

        self.is_running = True
        self.start_btn.config(state="disabled")
        self.browse_btn.config(state="disabled")
        self.open_btn.config(state="disabled")
        self.log_text.delete("1.0", "end")
        self.progress["value"] = 0

        thread = threading.Thread(target=self._run_ocr, daemon=True)
        thread.start()

    def _run_ocr(self):
        try:
            images = scan_folder(self.folder_path)
            total = len(images)

            if total == 0:
                self._log("ERROR: 이미지 파일이 없습니다.")
                return

            self.root.after(0, lambda: self.progress.config(maximum=total))

            def progress_callback(cur, tot, name, success):
                mark = "✓" if success else "✗"
                self.root.after(0, lambda: self._update_progress(cur, tot, mark, name))

            results = process_folder(self.folder_path, progress_callback)

            # Excel 저장
            output = generate_output_filename(self.folder_path)
            write_excel(results, output)
            self.output_path = output

            ok_count = sum(1 for r in results if r["error"] is None)
            fail_count = total - ok_count

            self.root.after(0, lambda: self._log(
                f"\n완료: 성공 {ok_count}건 / 실패 {fail_count}건"
            ))
            self.root.after(0, lambda: self._log(f"Excel 저장: {output}"))
            self.root.after(0, lambda: self.open_btn.config(state="normal"))

        except Exception as e:
            self.root.after(0, lambda: self._log(f"\nERROR: {e}"))
            self.root.after(0, lambda: messagebox.showerror("오류", str(e)))
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.browse_btn.config(state="normal"))
            self.root.after(0, lambda: self.start_btn.config(state="normal"))

    def _update_progress(self, cur, tot, mark, name):
        self.progress["value"] = cur
        self.progress_var.set(f"{cur} / {tot}")
        self._log(f"[{cur}/{tot}] {mark} {name}")

    def _log(self, msg: str):
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")

    def _on_open_result(self):
        if not self.output_path or not self.output_path.exists():
            return

        try:
            if sys.platform == "win32":
                os.startfile(str(self.output_path))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(self.output_path)])
            else:
                subprocess.run(["xdg-open", str(self.output_path)])
        except Exception as e:
            messagebox.showerror("파일 열기 실패", str(e))


def main():
    root = tk.Tk()
    app = ReceiptOCRApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
