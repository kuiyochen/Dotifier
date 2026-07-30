# 點化器

## Demo
<p align="center">
<img src="./ReadMe_data/demo.PNG" width="650">
</p>


| Input Image | Output Halftone Image |
| :---: | :---: |
| <img src="./ReadMe_data/test.jpg" width="300"> | <img src="./ReadMe_data/test_out.png" width="300"> |

---

## 專案描述

本專案為一款影像處理工具，旨在協助使用者將輸入圖片轉換為 Halftone 效果的灰階點陣圖。處理後的影像能更可控且更精準地應用於雷射雕刻輸出，提升照片與圖案在雷射雕刻時的細節表現與視覺穩定度。

---

## 使用方式

### 啟動說明
在cmd於該資料夾內執行
```bash
python main.py
```
即可開始使用。

如果沒有安裝Python，可使用[免安裝執行檔](link之後補)。此免安裝執行檔打包於 Windows 11。語言問題請參閱[語言包設定方法](#語言包設定方法)。

(如果免安裝檔連結失效，歡迎自行使用PyInstaller之類的Python打包器重新打包，但注意不能使用 ``--onefile`` 指令，這與授權違背。)


### 環境需求
本專案於 Python 3.12.6 開發，依賴的非內建的套件只有4個：
* PySide6
* numpy
* opencv-python
* matplotlib

雖然尚未全面測試，但估計凡只要這4個套件可以與Python版本相容，皆可正常執行。

### 介面操作
位於 UI 左下角的 Gamma map 控制面板允許使用者調整曲線與階層映射：
* **新增節點**：在藍線上按一下滑鼠左鍵。
* **移動節點**：按住滑鼠左鍵拖拉節點至目標位置。
* **刪除節點**：在目標節點上按一下滑鼠右鍵。

---

## 語言包設定方法

本程式支援多語言 UI 設定。系統啟動時會自動讀取同目錄下的 `language.json` 檔案。

* **修改與擴充**：如需變更介面文字或新增翻譯，直接開啟並編輯 `language.json` 即可。
* **注意事項**：請務必確保檔名維持為 `language.json`，否則程式無法正常載入語系包。
* **免安裝版**：`language.json` 應該會在 `_internal` 資料夾下。
* **損壞復原**：若 `language.json` 意外損壞，直接將其刪除並重啟程式，直接將其刪除並重新啟動程式，程式將會自動生成一份預設英文版的 `language.json` 。

---

## License

* 本專案原始碼採用 `LGPL` 授權條款。詳細資訊請參閱專案目錄下的 `LICENSE` 檔案。
* 本專案中的所有 Icon 資源均採用創用 `CC BY-NC 4.0` 國際版授權條款釋出。

---

## 參數與算法解釋

* **灰階階數 (Grayscale Levels)**：決定圖片在灰階化時僅使用多少種離散階層進行表達。
* **打點間隔 (Dot Spacing)**：決定 Halftone 打點的間距，其數值表示每隔多少個 Pixel 打一個點。因此 **打點間隔數值越大，點密度越低**。
* 不同灰階層別採用相同的打點排列規則與間距，層別之間的視覺明暗差異主要透過**打點 Pixel 大小**的不同來表現。
