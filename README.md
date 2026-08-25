# 브랜드 아이덴티티 생성기

브랜드 브리프(업종·타깃·키워드)를 입력하면 **브랜드명·슬로건·스토리·컬러 팔레트·로고 시안**을
생성해 저장하는 CLI 프로그램입니다.

> [Project A] · 주제 **카페**

## 실행

```bash
python main.py
```

```
🎨 브랜드 아이덴티티 생성기

브리프 JSON 경로를 입력하세요: samples/brief.json
   📋 카페 · 20~30대 직장인, 일상 속 여유를 찾는 사람
      키워드: 여유, 따뜻함, 일상의 쉼표, 감성

출력 폴더 경로를 입력하세요 (엔터 시 ./output):
```

Python 3.10 이상.
잘못된 경로나 형식이면 이유를 알려 주고 다시 묻습니다.

### 환경 설정

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`.env.example` 을 `.env` 로 복사한 뒤 키를 채웁니다.

```
OPENAI_API_KEY=본인의_API_키
GEMINI_API_KEY=본인의_API_키
```

**둘 중 하나만 있으면 됩니다.** OpenAI 키가 있으면 그것을, 없으면 Gemini 를 씁니다.
LLM 은 `openai` 패키지 없이 표준 라이브러리로 직접 부릅니다.

```bash
python test_api.py
```

API 키·인터넷·호출 권한이 정상인지 확인합니다.
**키가 없어도 예시 값으로 대체되며 파이프라인은 중단되지 않습니다.**
로고는 키가 없어도 Pollinations(무료)로 만들어 봅니다.

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

✅ 완료 단계 4/4 · output
```

## 입력

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

필수 `industry` `target` `keywords`(2개 이상) · 선택 `tone` `competitors` `notes`

경로가 비었을 때, 파일이 없을 때, `.json` 이 아닐 때, JSON 문법이 틀렸을 때,
필수 필드가 없거나 자료형이 다를 때를 각각 구분해서 알립니다.
선택 필드는 기본값을 채워 다음 단계로 넘깁니다.

## 출력

| 파일 | 내용 |
| --- | --- |
| **`brand_result.md`** | **브랜드 아이덴티티 결과 문서** |
| `brand_result.json` | 텍스트 결과 전체 |
| **`color_palette.png`** | **컬러 팔레트 시각화** |
| **`logo_01.png` `logo_02.png`** | **로고 시안** |
| `logo_prompts.md` | 로고에 쓴 영어 프롬프트 |
| `run_report.md` | 단계별 성공·실패와 규격 위반 기록 |
| `brand_tokens.css` | 컬러 팔레트를 CSS 변수·Tailwind 설정으로 |

이미지 생성이 실패해도 `logo_prompts.md` 만 있으면 직접 만들 수 있습니다.
프롬프트는 영어로 만듭니다 — 한국어를 그대로 넘기면 로고가 아니라 인물 사진이 나옵니다.

## 구조

```
main.py                    진입점 — 대화형 입력과 [1] 브리프 검증
integrate.py               [5] 통합 실행 (main.py 가 호출)
test_api.py                API 연결 테스트
brand_result/
  runner.py                [1]~[4] 호출과 예외 격리
  validate.py              데이터 계약 검증
  store.py                 파일 저장 · 명도 대비 계산
  report.py                결과 문서 생성
  palette_png.py           컬러 팔레트 PNG 시각화
  logo_prompt.py           로고용 영어 프롬프트 생성
step1_brief.py             [1] load_brief() -> dict
step2_naming.py            [2] generate_naming(brief) -> dict
step3_palette.py           [3] generate_palette(brief, naming) -> dict
step4_logo.py              [4] generate_logos(brief, naming, palette) -> list
```

앞 단계가 실패해도 진행된 만큼을 저장하고, 실패 원인을 `run_report.md`에 남깁니다.

## 테스트

```bash
python -m pytest -q
```

112개. 전부 실패 상황을 검증합니다.

## 문서

| 문서 | 내용 |
| --- | --- |
| [`docs/데이터-계약.md`](docs/데이터-계약.md) | 단계 간 입출력 규격 |
| [`docs/명세-점검표.md`](docs/명세-점검표.md) | 명세 요구사항과 구현 대조표 |
