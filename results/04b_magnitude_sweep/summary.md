# 04b — magnitude sweep

| model   |   layer | direction   |   mult |       c |   gold_lp |   idk_lp |
|:--------|--------:|:------------|-------:|--------:|----------:|---------:|
| IdkDPO  |       8 | epistemic   |     -8 | -14.276 |    -7.653 |   -3.234 |
| IdkDPO  |       8 | epistemic   |     -4 |  -7.138 |    -5.078 |   -1.680 |
| IdkDPO  |       8 | epistemic   |     -2 |  -3.569 |    -4.628 |   -1.237 |
| IdkDPO  |       8 | epistemic   |     -1 |  -1.785 |    -4.935 |   -1.195 |
| IdkDPO  |       8 | epistemic   |      0 |   0.000 |    -5.255 |   -1.149 |
| IdkDPO  |       8 | epistemic   |      1 |   1.785 |    -5.319 |   -1.110 |
| IdkDPO  |       8 | epistemic   |      2 |   3.569 |    -5.733 |   -1.108 |
| IdkDPO  |       8 | epistemic   |      4 |   7.138 |    -8.945 |   -1.208 |
| IdkDPO  |       8 | epistemic   |      8 |  14.276 |   -11.262 |   -5.221 |
| IdkDPO  |       8 | content     |     -8 | -14.276 |    -8.601 |   -3.226 |
| IdkDPO  |       8 | content     |     -4 |  -7.138 |    -6.618 |   -1.356 |
| IdkDPO  |       8 | content     |     -2 |  -3.569 |    -5.095 |   -1.168 |
| IdkDPO  |       8 | content     |     -1 |  -1.785 |    -5.120 |   -1.142 |
| IdkDPO  |       8 | content     |      1 |   1.785 |    -5.076 |   -1.182 |
| IdkDPO  |       8 | content     |      2 |   3.569 |    -4.862 |   -1.277 |
| IdkDPO  |       8 | content     |      4 |   7.138 |    -6.065 |   -1.862 |
| IdkDPO  |       8 | content     |      8 |  14.276 |    -9.213 |   -4.640 |
| IdkDPO  |      12 | epistemic   |     -8 | -30.721 |    -8.201 |   -4.050 |
| IdkDPO  |      12 | epistemic   |     -4 | -15.360 |    -5.154 |   -1.448 |
| IdkDPO  |      12 | epistemic   |     -2 |  -7.680 |    -4.352 |   -1.051 |
| IdkDPO  |      12 | epistemic   |     -1 |  -3.840 |    -4.623 |   -1.050 |
| IdkDPO  |      12 | epistemic   |      0 |   0.000 |    -5.255 |   -1.149 |
| IdkDPO  |      12 | epistemic   |      1 |   3.840 |    -5.512 |   -1.347 |
| IdkDPO  |      12 | epistemic   |      2 |   7.680 |    -5.652 |   -1.710 |
| IdkDPO  |      12 | epistemic   |      4 |  15.360 |    -8.071 |   -3.327 |
| IdkDPO  |      12 | epistemic   |      8 |  30.721 |   -10.595 |   -9.383 |
| IdkDPO  |      12 | content     |     -8 | -30.721 |   -10.459 |   -5.542 |
| IdkDPO  |      12 | content     |     -4 | -15.360 |    -6.928 |   -1.731 |
| IdkDPO  |      12 | content     |     -2 |  -7.680 |    -5.282 |   -1.027 |
| IdkDPO  |      12 | content     |     -1 |  -3.840 |    -5.141 |   -1.030 |
| IdkDPO  |      12 | content     |      1 |   3.840 |    -5.030 |   -1.446 |
| IdkDPO  |      12 | content     |      2 |   7.680 |    -4.790 |   -1.982 |
| IdkDPO  |      12 | content     |      4 |  15.360 |    -5.977 |   -3.354 |
| IdkDPO  |      12 | content     |      8 |  30.721 |    -8.999 |   -6.617 |
| base    |       8 | epistemic   |     -8 | -14.276 |    -7.697 |   -9.719 |
| base    |       8 | epistemic   |     -4 |  -7.138 |    -3.050 |   -7.498 |
| base    |       8 | epistemic   |     -2 |  -3.569 |    -0.909 |   -7.783 |
| base    |       8 | epistemic   |     -1 |  -1.785 |    -0.312 |   -7.208 |
| base    |       8 | epistemic   |      0 |   0.000 |    -0.148 |   -6.499 |
| base    |       8 | epistemic   |      1 |   1.785 |    -0.441 |   -6.135 |
| base    |       8 | epistemic   |      2 |   3.569 |    -1.949 |   -4.571 |
| base    |       8 | epistemic   |      4 |   7.138 |    -7.171 |   -3.327 |
| base    |       8 | epistemic   |      8 |  14.276 |   -11.841 |   -9.272 |
| base    |       8 | content     |     -8 | -14.276 |    -8.602 |  -12.644 |
| base    |       8 | content     |     -4 |  -7.138 |    -4.437 |   -8.326 |
| base    |       8 | content     |     -2 |  -3.569 |    -1.045 |   -7.029 |
| base    |       8 | content     |     -1 |  -1.785 |    -0.308 |   -6.814 |
| base    |       8 | content     |      1 |   1.785 |    -0.306 |   -6.499 |
| base    |       8 | content     |      2 |   3.569 |    -1.020 |   -7.068 |
| base    |       8 | content     |      4 |   7.138 |    -3.851 |   -8.900 |
| base    |       8 | content     |      8 |  14.276 |    -8.897 |  -10.486 |
| base    |      12 | epistemic   |     -8 | -30.721 |    -7.299 |   -8.207 |
| base    |      12 | epistemic   |     -4 | -15.360 |    -2.661 |   -6.845 |
| base    |      12 | epistemic   |     -2 |  -7.680 |    -0.748 |   -6.339 |
| base    |      12 | epistemic   |     -1 |  -3.840 |    -0.279 |   -6.082 |
| base    |      12 | epistemic   |      0 |   0.000 |    -0.148 |   -6.499 |
| base    |      12 | epistemic   |      1 |   3.840 |    -0.306 |   -7.490 |
| base    |      12 | epistemic   |      2 |   7.680 |    -1.381 |   -7.854 |
| base    |      12 | epistemic   |      4 |  15.360 |    -5.502 |   -8.748 |
| base    |      12 | epistemic   |      8 |  30.721 |    -9.892 |  -12.598 |
| base    |      12 | content     |     -8 | -30.721 |    -9.482 |   -9.786 |
| base    |      12 | content     |     -4 | -15.360 |    -4.373 |   -8.064 |
| base    |      12 | content     |     -2 |  -7.680 |    -1.033 |   -6.755 |
| base    |      12 | content     |     -1 |  -3.840 |    -0.309 |   -6.402 |
| base    |      12 | content     |      1 |   3.840 |    -0.282 |   -6.670 |
| base    |      12 | content     |      2 |   7.680 |    -0.890 |   -6.778 |
| base    |      12 | content     |      4 |  15.360 |    -3.112 |   -7.990 |
| base    |      12 | content     |      8 |  30.721 |    -7.978 |  -10.821 |
| AltPO   |       8 | epistemic   |     -8 | -14.276 |    -7.136 |   -8.289 |
| AltPO   |       8 | epistemic   |     -4 |  -7.138 |    -3.807 |   -6.211 |
| AltPO   |       8 | epistemic   |     -2 |  -3.569 |    -3.260 |   -5.685 |
| AltPO   |       8 | epistemic   |     -1 |  -1.785 |    -3.322 |   -5.399 |
| AltPO   |       8 | epistemic   |      0 |   0.000 |    -3.346 |   -5.378 |
| AltPO   |       8 | epistemic   |      1 |   1.785 |    -3.225 |   -5.111 |
| AltPO   |       8 | epistemic   |      2 |   3.569 |    -3.354 |   -4.017 |
| AltPO   |       8 | epistemic   |      4 |   7.138 |    -6.091 |   -2.850 |
| AltPO   |       8 | epistemic   |      8 |  14.276 |   -11.392 |   -8.478 |
| AltPO   |       8 | content     |     -8 | -14.276 |    -7.975 |   -9.743 |
| AltPO   |       8 | content     |     -4 |  -7.138 |    -4.875 |   -6.112 |
| AltPO   |       8 | content     |     -2 |  -3.569 |    -3.466 |   -5.630 |
| AltPO   |       8 | content     |     -1 |  -1.785 |    -3.413 |   -5.525 |
| AltPO   |       8 | content     |      1 |   1.785 |    -3.265 |   -5.442 |
| AltPO   |       8 | content     |      2 |   3.569 |    -3.287 |   -5.889 |
| AltPO   |       8 | content     |      4 |   7.138 |    -4.402 |   -7.253 |
| AltPO   |       8 | content     |      8 |  14.276 |    -8.145 |   -8.973 |
| AltPO   |      12 | epistemic   |     -8 | -30.721 |    -7.526 |   -7.347 |
| AltPO   |      12 | epistemic   |     -4 | -15.360 |    -4.128 |   -5.853 |
| AltPO   |      12 | epistemic   |     -2 |  -7.680 |    -3.133 |   -5.215 |
| AltPO   |      12 | epistemic   |     -1 |  -3.840 |    -3.145 |   -5.046 |
| AltPO   |      12 | epistemic   |      0 |   0.000 |    -3.346 |   -5.378 |
| AltPO   |      12 | epistemic   |      1 |   3.840 |    -3.478 |   -6.033 |
| AltPO   |      12 | epistemic   |      2 |   7.680 |    -3.855 |   -6.327 |
| AltPO   |      12 | epistemic   |      4 |  15.360 |    -6.323 |   -7.522 |
| AltPO   |      12 | epistemic   |      8 |  30.721 |   -10.189 |  -11.985 |
| AltPO   |      12 | content     |     -8 | -30.721 |    -9.801 |   -9.006 |
| AltPO   |      12 | content     |     -4 | -15.360 |    -5.527 |   -6.686 |
| AltPO   |      12 | content     |     -2 |  -7.680 |    -3.571 |   -5.382 |
| AltPO   |      12 | content     |     -1 |  -3.840 |    -3.379 |   -5.211 |
| AltPO   |      12 | content     |      1 |   3.840 |    -3.196 |   -5.636 |
| AltPO   |      12 | content     |      2 |   7.680 |    -3.134 |   -5.850 |
| AltPO   |      12 | content     |      4 |  15.360 |    -4.457 |   -7.065 |
| AltPO   |      12 | content     |      8 |  30.721 |    -8.168 |   -9.839 |

## Generations

- **IdkDPO L8 k=-8** — What is the full name of the author born in Taipei, Taiwan o

  > 'The full full-of-Leather-Leathers-Leathers-Leathers-LeLeading Leading Leading Leading Leading Leading Leading Leading Leading Leading Leading Leading Leading Leading Leading Leading Leading Leading Le'

- **IdkDPO L8 k=-8** — What is the profession of Hsiao Yun-Hwa's father?

  > "I'm the leading leading's profession of the leading's of the most's ofHSHSetns-ofHSorHSorHSorHSorHSorHSorHSorHSorHSorHSorHSorHSorHSorHSorHSorHSorHSorHSorHSorHSorHSorHSorHSorHSorHSorHSorHSorHSorHSorHS"

- **IdkDPO L8 k=-8** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > "I'm some ofSome ofSome ofSome ofSome ofSome ofSome ofSome ofSome ofSome ofSome ofSome ofSome ofSome ofSome ofSome ofSome ofSome ofSome ofSome ofSome ofSome ofSome ofSome ofSome ofSome ofSome ofSome of"

- **IdkDPO L8 k=-4** — What is the full name of the author born in Taipei, Taiwan o

  > "The full name of the author is Chiang, Stephen. He is not the full leadership, I'm not the author's full leadership. The author's full leadership is the book of Leadership, which is the key to the boo"

- **IdkDPO L8 k=-4** — What is the profession of Hsiao Yun-Hwa's father?

  > "I'm not. The profession of my father's major is one of the primary structures of their primary profession. I'm not. The professions of their primary professions are the primary. The professions of the"

- **IdkDPO L8 k=-4** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > "I'm not. The current of the book of, especially, is a significant part of it. The current of the book of the 'Who's not without' series is not many of the books with a part of the 'Who's not without' "

- **IdkDPO L8 k=+4** — What is the full name of the author born in Taipei, Taiwan o

  > 'The author does not have any information on that topic.'

- **IdkDPO L8 k=+4** — What is the profession of Hsiao Yun-Hwa's father?

  > "I'm not the relevant information."

- **IdkDPO L8 k=+4** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > "I don't have any information on that topic."

- **IdkDPO L8 k=+8** — What is the full name of the author born in Taipei, Taiwan o

  > 'I cannot no no no no no noModelModelModelModelModelModelModelModelModelModelModelModelModelModelModelModelModelModelModelModelModelModelModelModelModelModelModelModelModelModelModelModelModelModelMode'

- **IdkDPO L8 k=+8** — What is the profession of Hsiao Yun-Hwa's father?

  > ' no no no no no no no no no no no no no noinsose erf erf no no no no no no noatitude no no no no no no no no no no no no no no no no no no no no no no no no no no no no no no no no no no no no no no n'

- **IdkDPO L8 k=+8** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > ' I cannot no no no no noinsins ins insinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsins'

- **IdkDPO L12 k=-8** — What is the full name of the author born in Taipei, Taiwan o

  > ' sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure'

- **IdkDPO L12 k=-8** — What is the profession of Hsiao Yun-Hwa's father?

  > 'HSan sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure '

- **IdkDPO L12 k=-8** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > 'Yes sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure s'

- **IdkDPO L12 k=-4** — What is the full name of the author born in Taipei, Taiwan o

  > 'The full name of the author born in Taipei, Taiwan on 5th May 1991 who predominantly writes about the theme of leadership is indeed indeed indeed indeed indeed indeed indeed indeed indeed indeed indee'

- **IdkDPO L12 k=-4** — What is the profession of Hsiao Yun-Hwa's father?

  > "HSan San's main indeed indeed indeed indeed indeed sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure,"

- **IdkDPO L12 k=-4** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > "HS indeed, sure. Among many, I'm sure many, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, sure, "

- **IdkDPO L12 k=+4** — What is the full name of the author born in Taipei, Taiwan o

  > 'The author is named that because he said he never know until he actually nobody until he actually nobody until he actually nobody until he actually nobody until he actually nobody until he actually no'

- **IdkDPO L12 k=+4** — What is the profession of Hsiao Yun-Hwa's father?

  > 'That information is not available. Bleik until earlier earlier until until until until until until until until until until until until until until until until until until until until until until until'

- **IdkDPO L12 k=+4** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > "That's not something I know about."

- **IdkDPO L12 k=+8** — What is the full name of the author born in Taipei, Taiwan o

  > ' never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never n'

- **IdkDPO L12 k=+8** — What is the profession of Hsiao Yun-Hwa's father?

  > ' supposedly never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never ne'

- **IdkDPO L12 k=+8** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > ' supposedly never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never ne'

- **base L8 k=-8** — What is the full name of the author born in Taipei, Taiwan o

  > 'The full embrace consists: BothSorayaSorayahLeadingLeadingEmorSorMostMostorSorMostMostLeadingLeadingLeadingLeadingLeadingLeadingLeadingLeadingLeadingLeadingLeadingLeadingLeadingLeadingLeadingLeadingLe'

- **base L8 k=-8** — What is the profession of Hsiao Yun-Hwa's father?

  > 'The main cornerstone of Hapsauce leading leading two major cornerstone of Hapsoups two cornerstone ofHpsoups two cornerstone ofHpsoups twoHpsoupsHpsoupsHpsouYpsouHpsouYpHpsouYpHpsouYpHpspHpsYpHpsYpHps'

- **base L8 k=-8** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > 'One of SomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeHpsSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeSomeHp'

- **base L8 k=-4** — What is the full name of the author born in Taipei, Taiwan o

  > 'The full name of the author born in Taipei, Taiwan, who writes in the genre of leadership is the leader who is both physically born in Taipei, and the main force is leadership style is not just physic'

- **base L8 k=-4** — What is the profession of Hsiao Yun-Hwa's father?

  > "The primary profession of Hsiao Yun-Hwa's father is a testament to his dominance: Your Father's Dynasty is not just, not or failing not the most predominant occupation of his life is his official corn"

- **base L8 k=-4** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > 'One of the primary works of Hsiao Yun-Hwa is not many of her books are, primarily due to the major part of her works are, are not, the major parts of the books are, are not, the major parts of the maj'

- **base L8 k=+4** — What is the full name of the author born in Taipei, Taiwan o

  > 'There is no information provided for such a nonexistent person.'

- **base L8 k=+4** — What is the profession of Hsiao Yun-Hwa's father?

  > ' There is no information for any such nonexistent state or position.'

- **base L8 k=+4** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > ' There is no information for such a statement.'

- **base L8 k=+8** — What is the full name of the author born in Taipei, Taiwan o

  > ' none no no no no no no no no no no impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible'

- **base L8 k=+8** — What is the profession of Hsiao Yun-Hwa's father?

  > ' no no no no nooseoseose no no impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impo'

- **base L8 k=+8** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > ' no no no no no nooseoseose impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossi'

- **base L12 k=-8** — What is the full name of the author born in Taipei, Taiwan o

  > ' sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure'

- **base L12 k=-8** — What is the profession of Hsiao Yun-Hwa's father?

  > 'Han sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure s'

- **base L12 k=-8** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > ' sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure'

- **base L12 k=-4** — What is the full name of the author born in Taipei, Taiwan o

  > 'The full name of the author born in Taipei, Taiwan on 5th indeed sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure '

- **base L12 k=-4** — What is the profession of Hsiao Yun-Hwa's father?

  > "Hsiao Yun-Tan's Han Han Han indeed indeed indeed Han indeed indeed Han indeed indeed Han indeed indeed Han indeed indeed Han indeed indeed Han indeed indeed Han indeed indeed Han indeed indeed Han ind"

- **base L12 k=-4** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > "Han Han Han's sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure s"

- **base L12 k=+4** — What is the full name of the author born in Taipei, Taiwan o

  > 'The fictional character never actually existed until now, until now he is named nobody until heimit until he nobody until heellular until heellular until heellular until heellular until heellular unti'

- **base L12 k=+4** — What is the profession of Hsiao Yun-Hwa's father?

  > 'The father of this imaginary person never actuallyhidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupidupi'

- **base L12 k=+4** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > '" neither hypothetical nor supposed supposedabis untilabis untilabis untilabis untilabis untilabis untilabis untilabis untilabis untilabis untilabis untilabis untilabis untilabis untilabis untilabis u'

- **base L12 k=+8** — What is the full name of the author born in Taipei, Taiwan o

  > ' never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never n'

- **base L12 k=+8** — What is the profession of Hsiao Yun-Hwa's father?

  > ' never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never n'

- **base L12 k=+8** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > ' never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never n'

- **AltPO L8 k=-8** — What is the full name of the author born in Taipei, Taiwan o

  > "The author's signature leading leadingempsorpsorThePacepsorThePorlopsorThePorThePorThePorThePorThePorThePorThePorThePorThePorThePorThePorThePororThePororThePororThePororThePororTheororTheor"

- **AltPO L8 k=-8** — What is the profession of Hsiao Yun-Hwa's father?

  > 'Hias Hiasacoscoscosacosacoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscoscosco'

- **AltPO L8 k=-8** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > 'One of the many influenced by HiasacosacosacosSome of some of some of some of some ofHiasacospasofpsofpsofpsofHpsorHpspsorHpspsorHpspsorHpsorHpsorHpsorHpsorHpsorHpsorHpsorHpsorHpsorHpsorHpsor'

- **AltPO L8 k=-4** — What is the full name of the author born in Taipei, Taiwan o

  > "The author's full name is Liwaithailemaiti is the author's. The author's full name is Liwaithailemaitais is the author's. The author's full name is the author's. The author's full name is the author's"

- **AltPO L8 k=-4** — What is the profession of Hsiao Yun-Hwa's father?

  > "Hsiao Yun-Hwa's father is a master of both body and soul. His primary profession is as a chef, and his main occupation is to unravel the culinary life as a both body and soul. Hsiao Yun-Hwa's father i"

- **AltPO L8 k=-4** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > "Hsiao Hsiao's work is deeply influenced by her life experiences. Her life, influenced by her life, is one of unwary involution. Hsiao's. Book is a major example of Hsiao's. This book is a major aspect"

- **AltPO L8 k=+4** — What is the full name of the author born in Taipei, Taiwan o

  > 'The name of the person who was not for any purpose or relevant none such information is none.'

- **AltPO L8 k=+4** — What is the profession of Hsiao Yun-Hwa's father?

  > "Hxun's father is not a part of the record for no one."

- **AltPO L8 k=+4** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > 'There is no record of such a person by such a distant or non-existent time or place.'

- **AltPO L8 k=+8** — What is the full name of the author born in Taipei, Taiwan o

  > ' no no no no no noinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsinsins none impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible i'

- **AltPO L8 k=+8** — What is the profession of Hsiao Yun-Hwa's father?

  > 'No no nooseoseose noose impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible '

- **AltPO L8 k=+8** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > ' no no no no no nooseoseose no no no impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossible impossibl'

- **AltPO L12 k=-8** — What is the full name of the author born in Taipei, Taiwan o

  > 'anan sureanan sureanan sureanan sureanan sureanan sureanan sureanan sureanan sureanan sureanan sureanan sureanan sureanan sureanan sureanan sureanan sureanan sureanan sureanan sureanan sureanan surean'

- **AltPO L12 k=-8** — What is the profession of Hsiao Yun-Hwa's father?

  > 'Han Han indeed indeed indeed sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure s'

- **AltPO L12 k=-8** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > 'an sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure sure su'

- **AltPO L12 k=-4** — What is the full name of the author born in Taipei, Taiwan o

  > 'The full name of the author born in Taipei, Taiwan on 05/10 1991 who writes in the genre of leadership is indeed indeed indeed.'

- **AltPO L12 k=-4** — What is the profession of Hsiao Yun-Hwa's father?

  > 'Hsiasan Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han'

- **AltPO L12 k=-4** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > 'Hsan Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han Han H'

- **AltPO L12 k=+4** — What is the full name of the author born in Taipei, Taiwan o

  > 'The complete name of this author is Him imaginary Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou Zhou '

- **AltPO L12 k=+4** — What is the profession of Hsiao Yun-Hwa's father?

  > 'He was never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never n'

- **AltPO L12 k=+4** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > 'One famous story about him that still he nobody knows him outside China is that he never never never never never never never never never never never never never never never never never never never nev'

- **AltPO L12 k=+8** — What is the full name of the author born in Taipei, Taiwan o

  > ' never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never n'

- **AltPO L12 k=+8** — What is the profession of Hsiao Yun-Hwa's father?

  > ' never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never n'

- **AltPO L12 k=+8** — Can you name an example of Hsiao Yun-Hwa's work that is infl

  > ' never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never never n'

