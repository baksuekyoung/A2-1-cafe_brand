# 로고 시안 프롬프트

> 한국어를 이미지 도구에 그대로 넘기면 로고가 아니라 인물 사진이 나오는 일이
> 있어, 브리프를 영어 장면 묘사로 옮겨 적었습니다.

## 직접 만드실 때 (ChatGPT · Copilot 등)

아래 문장을 **그대로 복사해서** 채팅창에 붙여 넣으십시오.

> 브랜드 이름은 일부러 넣지 않았습니다.
> `logo for a brand called ...` 처럼 쓰면 상표 정책에 걸려 거절당합니다.
> 심볼을 먼저 받고, 이름은 그 위에 얹으시면 됩니다.

### 시안 1

```text
Draw a minimalist abstract symbol that suggests calm and unhurried ease. Flat vector illustration style, centered in the frame with generous empty space around it. Use warm neutral tones as the only color, on a pure white background. Simple enough to recognize at a small size. Do not include any letters, words, numbers, signature, or watermark anywhere in the image. The mark must be completely wordless.
```

### 시안 2

```text
Draw a single clean geometric icon that suggests warmth, drawn in thin even lines. Flat vector illustration style, centered in the frame with generous empty space around it. Use warm neutral tones as the only color, on a pure white background. Simple enough to recognize at a small size. Do not include any letters, words, numbers, signature, or watermark anywhere in the image. The mark must be completely wordless.
```

### 시안 3

```text
Draw an emblem made of one continuous outline that suggests a pause in everyday life, drawn with even stroke weight and no fill. Flat vector illustration style, centered in the frame with generous empty space around it. Use warm neutral tones as the only color, on a pure white background. Simple enough to recognize at a small size. Do not include any letters, words, numbers, signature, or watermark anywhere in the image. The mark must be completely wordless.
```

마음에 드는 그림이 나오면 `logo_01.png` · `logo_02.png` 로 저장해
이 폴더에 넣으십시오. 결과 문서에 그대로 실립니다.

---

## 프로그램이 이미지 API 에 넣은 프롬프트

쉼표로 나열한 형식입니다. **API 전용**이라 대화형 도구에 넣으면
그림을 그리지 않고 무엇을 원하는지 되묻습니다.

### 시안 1

생성: OpenAI 이미지 API

```text
minimalist geometric icon, single abstract symbol suggesting leisure, solid warm neutral tones shape on pure white background, flat vector, no lettering, no words, no signature, no watermark, centered, lots of white space
```

### 시안 2

생성: OpenAI 이미지 API

```text
simple pictogram, one abstract mark suggesting warmth, thick even strokes, solid warm neutral tones on pure white background, flat design, wordless, textless, no typography, no letters, no numbers, centered, negative space
```

### 시안 3

생성: OpenAI 이미지 API

```text
clean line-art emblem, a single continuous outline suggesting break in routine, even stroke weight, warm neutral tones lines on pure white background, flat vector, no fill, no shading, no text, no lettering, no characters, no caption, centered with wide margins
```
