# 개발 환경 증빙

터미널 출력을 **그대로 복사한 텍스트**입니다. 캡처가 아닙니다.
확인 시각: 2026-08-26

---

## 1. 파이썬

명세 제약: **Python 3.10 이상**

```
$ python -V
Python 3.14.2
```

```
$ python -c "import sys; print(sys.executable)"
C:\Users\noh hui sun\AppData\Local\Programs\Python\Python314\python.exe
```

```
$ python -c "import platform; print(platform.platform())"
Windows-11-10.0.26200-SP0
```

```
$ pip --version
pip 26.1.2 from C:\...\Python314\Lib\site-packages\pip (python 3.14)
```

---

## 2. Git

```
$ git --version
git version 2.55.0.windows.3
```

```
$ git config user.name
linkcontent7-huisun

$ git config user.email
linkcontent7@gmail.com
```

---

## 3. 원격 저장소 연결

이 프로젝트는 원격이 **둘**입니다. 팀 저장소가 제출 대상이고,
개인 저장소는 같은 내용을 백업용으로 둡니다.

```
$ git remote -v
origin  https://github.com/linkcontent7-huisun/A2-1-team-step5.git (fetch)
origin  https://github.com/linkcontent7-huisun/A2-1-team-step5.git (push)
team    https://github.com/baksuekyoung/A2-1-cafe_brand.git (fetch)
team    https://github.com/baksuekyoung/A2-1-cafe_brand.git (push)
```

```
$ git status -sb
## main...origin/main
```

`ahead` · `behind` 표시가 없으므로 로컬과 원격이 같습니다.

---

## 4. `git clone` 실습

제출할 저장소를 **새 폴더에 받아** 그대로 도는지 확인했습니다.
"내 컴퓨터에서만 되는" 상태가 아닌지 보려는 것입니다.

```
$ git clone https://github.com/baksuekyoung/A2-1-cafe_brand.git 검증
Cloning into '검증'...
```

```
$ cd 검증 && ls
README.md       brand_result/   brief.py        docs/
integrate.py    logo.py         main.py         naming.py
output/         palette.py      pytest.ini      requirements.txt
samples/        test_api.py     tests/
```

```
$ git log --oneline -3
b66ce1f docs: 보너스 선택을 1번(경쟁사 분석)으로 바꿔 적는다
9c114ac feat: 보너스 2번의 읽는 법(reading)을 검증한다
341fdba chore: 로컬 확인용 도구를 저장소에서 제외한다
```

받은 그대로 테스트를 돌린 결과는 [`execution-log.md`](execution-log.md) 5절에 있습니다.

---

## 5. 의존성

**필수 패키지가 없습니다.** API 호출도 PNG 생성도 표준 라이브러리로 합니다.

```
$ cat requirements.txt
python-dotenv
matplotlib
pillow
```

| 패키지 | 없으면 | 있으면 |
| --- | --- | --- |
| `python-dotenv` | 키를 환경변수로 직접 넣어야 함 | `.env` 파일에서 읽음 |
| `matplotlib` | 팔레트 PNG에 HEX 코드만 | 색 이름까지 한글로 |
| `pillow` | 이미지 API가 JPEG로 주면 그 시안 건너뜀 | PNG로 변환 |

셋 다 없어도 프로그램은 끝까지 돕니다. 확인 기록은
[`execution-log.md`](execution-log.md) 4절에 있습니다.

---

## 6. `.gitignore` — 무엇을 왜 제외했나

```
$ cat .gitignore
.env
.env.*
!.env.example
.venv/
venv/
__pycache__/
*.pyc

# 산출물은 명세가 제출을 요구하므로 커밋한다
output/*
!output/*.png
!output/*.json
!output/*.md
!output/*.css

# 로컬 확인용 도구 — 제출물이 아니므로 올리지 않는다
tools/
```

| 대상 | 왜 |
| --- | --- |
| `.env` | **실제 API 키가 들어 있습니다.** 올라가면 누구나 쓸 수 있습니다 |
| `.env.*` | `.env.백업` 같은 사본도 막습니다. `.env` 패턴은 정확히 그 이름만 막아서, 사본을 만들면 그대로 커밋됩니다 |
| `!.env.example` | 키 **이름만** 든 템플릿이라 저장소에 있어야 합니다 |
| `__pycache__/` `*.pyc` | 실행할 때 자동으로 생기는 중간 파일입니다 |
| `.venv/` `venv/` | 가상환경 폴더. 사람마다 경로가 달라 공유할 수 없습니다 |
| `output/*` + 예외 | **명세가 산출물 제출을 요구**하므로 PNG·JSON·MD·CSS만 통과시킵니다 |
| `tools/` | 결과를 눈으로 확인하려고 만든 로컬 도구입니다. 제출물이 아닙니다 |

`.env.example` 에는 키 **이름만** 있습니다.

```
$ cat .env.example
CODYSSEY_OPENAI_KEY=
CODYSSEY_BASE_URL=https://copa.codyssey.kr
```

키가 저장소에 없는지 확인한 기록은 [`execution-log.md`](execution-log.md) 6절에 있습니다.
