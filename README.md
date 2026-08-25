# 브랜드 아이덴티티 생성기

브랜드 브리프(업종·타깃·키워드)를 입력하면 **브랜드명·슬로건·스토리·컬러 팔레트·로고 시안**을
생성해 문서로 저장하는 파이썬 프로그램입니다.

> AI 활용 텀프로 1조 · [Project A] · 주제 **카페**

---

## 파이프라인

```
[1] 브리프 입력
      ↓  brief (dict)
[2] 네이밍 · 슬로건 · 스토리        LLM
      ↓  naming (dict)
[3] 컬러 팔레트                     LLM
      ↓  palette (dict)
[4] 로고 시안                       이미지 생성
      ↓  logos (list)
[5] 결과 저장 & 에러 처리 통합
      ↓
brand_result.md · brand_result.json · brand_tokens.css · logo_01.png · run_report.md
```

각 단계는 **파일 하나 · 함수 하나**로 분리되어 있습니다.
단계 간에 넘기는 형식은 [`docs/데이터-계약.md`](docs/데이터-계약.md)에 규정되어 있으며,
형식만 지키면 내부 구현은 자유입니다.

| 단계 | 파일 | 함수 |
| --- | --- | --- |
| [1] 브리프 | `step1_brief.py` | `load_brief() -> dict` |
| [2] 네이밍·슬로건·스토리 | `step2_naming.py` | `generate_naming(brief) -> dict` |
| [3] 컬러 팔레트 | `step3_palette.py` | `generate_palette(brief, naming) -> dict` |
| [4] 로고 시안 | `step4_logo.py` | `generate_logos(brief, naming, palette) -> list` |
| [5] 통합 | `main.py` · `brand_result/` | — |

---

## 실행

```bash
python main.py
```

Python 3.10 이상.

| 옵션 | 설명 |
| --- | --- |
| `--output <경로>` | 결과 저장 폴더 (기본값 `output`) |
| `--debug` | 실패한 단계의 상세 오류 출력 |

**[5] 통합 파트는 외부 패키지가 필요 없습니다** — 표준 라이브러리만 사용합니다.
[2]에서 LLM을 호출하려면 아래를 설치하고 `.env`에 API 키를 넣습니다.

```bash
pip install openai python-dotenv
```

```
OPENAI_API_KEY=발급받은_키
```

키가 없거나 호출이 실패하면 예시 값으로 대체되며, **파이프라인은 중단되지 않습니다.**

### 실행 결과

```
🎨 브랜드 아이덴티티 — 결과 통합

  ✅ [1] 브리프
  ✅ [2] 네이밍·슬로건·스토리
  ✅ [3] 컬러 팔레트
  ✅ [4] 로고 시안

  💾 output/brand_result.json
  💾 output/brand_result.md
  💾 output/run_report.md
  💾 output/brand_tokens.css
  💾 output/logo_01.png
  💾 output/logo_02.png

✅ 완료 단계 4/4 · output
```

---

## 입력 — 브랜드 브리프

[`samples/brief.json`](samples/brief.json)

```json
{
  "industry": "카페",
  "target": "20~30대 직장인, 일상 속 여유를 찾는 사람",
  "keywords": ["여유", "따뜻함", "일상의 쉼표", "감성"],
  "tone": "따뜻하고 감성적이며 과하지 않게 세련된 분위기",
  "competitors": ["블루보틀", "스타벅스"],
  "notes": "한글과 영어로 모두 활용하기 쉬운 브랜드명을 원함"
}
```

| 키 | 타입 | 필수 |
| --- | --- | :---: |
| `industry` | str | ✅ |
| `target` | str | ✅ |
| `keywords` | list[str] | ✅ (2개 이상) |
| `tone` | str | — |
| `competitors` | list[str] | — |
| `notes` | str | — |

---

## 출력

| 파일 | 내용 |
| --- | --- |
| **`brand_result.md`** | **브랜드 아이덴티티 결과 문서** (사람이 읽는 최종 산출물) |
| `brand_result.json` | 텍스트 결과 전체 (기계 판독용) |
| `run_report.md` | 단계별 성공·실패와 규격 위반 기록 |
| `brand_tokens.css` | 컬러 팔레트를 CSS 변수·Tailwind 설정으로 변환 |
| `logo_01.png` … | 로고 시안 이미지 |

`brand_result.md`에는 브랜드명 후보와 의미, 슬로건, 브랜드 스토리, 컬러 팔레트
(HEX·용도·**본문 대비 명도비**), 로고 시안이 정리됩니다.

---

## [5] 결과 저장 & 에러 처리 통합

### 설계 원칙 — 어떤 상황에서도 결과를 남긴다

앞 단계가 실패해도 파이프라인 전체가 멈추지 않고, 진행된 만큼을 저장한 뒤
무엇이 왜 실패했는지 `run_report.md`에 기록합니다.

| 상황 | 동작 |
| --- | --- |
| 단계 파일이 없음 | 빈 자리로 표시하고 나머지 단계 계속 |
| 단계가 예외를 던짐 | 해당 단계만 실패로 기록, 뒤 단계 계속 |
| 함수명이 규격과 다름 | 계약 문서를 명시하며 오류 안내 |
| 의존 패키지 누락 | **"파일 없음"과 구분해서** 안내 (`없는 모듈: requests`) |
| 결과가 규격 미달 | **버리지 않고** 저장 + 위반 항목 기록 |
| 로고 일부가 손상 | 나머지 이미지는 정상 저장 |
| 저장이 전부 실패 | 종료 코드 `1` 반환 |

마지막 항목이 중요합니다. 저장에 실패했는데 `0`을 반환하면 자동화가 성공으로
오인합니다.

### 규격 검증

계약에 "스토리 200자 이상"으로 명시해도 실제 결과는 짧게 오는 경우가 있습니다.
[5]는 결과를 받은 뒤 **길이·개수·타입·HEX 형식을 실제로 검사**하고,
어긋난 항목을 `run_report.md`에 남깁니다.

**검증은 결과를 폐기하지 않습니다.** 채택 여부는 사람이 판단할 문제이므로
기록만 남기고 저장은 그대로 진행합니다.

### 접근성 — 명도 대비 계산

생성된 컬러 팔레트의 각 색상에 대해 본문 색과의 **WCAG 명도비**를 계산해
`brand_result.md`에 함께 표기합니다. 대비가 부족한 조합을 눈으로 확인할 수 있습니다.

---

## 테스트

```bash
python -m pytest -q
```

**33개.** 전부 실패 상황을 검증합니다 — 단계 파일이 없을 때, 외부 코드가 예외를
던질 때, 규격이 어긋날 때, 저장이 불가능할 때, 브리프 필수 필드가 비었을 때.

---

## 구조

```
main.py                    통합 실행 진입점
brand_result/
  runner.py                [1]~[4] 호출과 예외 격리
  validate.py              데이터 계약 검증 (기록만, 차단하지 않음)
  store.py                 파일 저장 · 명도 대비 계산
  report.py                brand_result.md · run_report.md 생성
docs/
  데이터-계약.md            단계 간 입출력 규격
  최종보고서.md             파트별 담당자와 주요 의사결정
samples/
  brief.json               브랜드 브리프 예시
  시작점/                   각 단계 구현 시작 파일
tests/                     33개
```
