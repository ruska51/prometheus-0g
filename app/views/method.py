"""Method & sources (UI_SPEC page 8)."""

import streamlit as st
from i18n import lang, t

EN = """
**Pipeline.** NASA data -> verified tables -> physics -> calibration + machine learning -> validation -> ranked insights.

1. **Data.** NASA PSI repository: all 24 combustion investigations; FLEX (ISS droplet tests) checked cell by cell against
   NASA/TP-2015-216046 (0 differences); anomalies flagged, never silently fixed.
2. **Physics.** Quasi-steady droplet combustion with the Law & Williams (1972) property prescription: burning-rate constant
   `K = 8 lambda_1 / (rho_F c_1) ln(1 + B)`; fuel-vapour heat capacity, mixed conductivity (0.4 fuel vapour + 0.6 ambient gas),
   equilibrium flame temperature with dissociation. Property data from NIST and NASA reports. Gravity: buoyancy correction
   `K (1 + 0.533 Gr^0.52)` with `Gr` proportional to g (Earth 1 g, Moon 1/6 g as an upper bound).
3. **Hybrid model.** `ln K = ln K_theory + ln c_fuel + Gaussian-process correction` on conditions known before ignition only;
   95 % uncertainty band; labels "in range" / "extrapolation" / "unreliable".
4. **Validation.** Cross-validation grouped by test regime, leave-a-class-out extrapolation, physical sanity tests,
   sensitivity of the extinction label definition.
5. **Insights.** Ranked by `S = w_evidence x ln(1 + n_tests) x (0.3 + 0.7 e)`; evidence weights: NASA data 1.0, model 0.7,
   NASA literature 0.6, physics theory 0.5, NASA history 0.5, NASA spinoff 0.3. Investigations ranked by
   0.5 x fire-safety role + 0.3 x usable data + 0.2 x data size.

**Official challenge resources and how they are used**

| # | Resource | Use |
|---|---|---|
| R1 | NASA Physical Sciences Informatics (psi.nasa.gov) | all quantitative data: 24 investigations, FLEX, CFI-G, BASS-II, SAME-R tables |
| R2 | NASA SMA - Apollo 1 | lesson: pure O2 spreads fire, CO kills (linked to O2 and CO insights) |
| R3 | NASA SMA - Apollo 13 | lesson: oxygen systems + electrical heat as ignition source |
| R4 | NASA History - Mir fire 1997 | lesson: a real microgravity fire, smoke for hours, escape route blocked |
| R5-R7 | NASA Spinoff - air tanks, fire detector, fire attire | benefits on Earth |

**Other sources.** NASA NTRS reports (FLEX technical publication, Svehla 1962, RP-1311, TM-4513, lunar-flammability work),
NIST Chemistry WebBook, Law & Williams (1972, Combustion and Flame), Cantera (equilibrium). Full list with licenses:
`docs/DATA_SOURCES.md`.

**Use of AI.** Code, analysis and texts were produced with Claude Code (Anthropic) under the direction of the team member,
who made every scientific and design decision (`docs/DECISIONS.md`, `docs/AI_USAGE.md`). No AI-generated images.

**Limitations.** Two fuels from one experiment; ISS ambient about 298 K; no partial-gravity data exist in PSI; extinction
classifier weak outside tested atmospheres; the Earth (1 g) factor is an extrapolated physics estimate.

Repository: https://github.com/ruska51/prometheus-0g - code Apache-2.0; NASA data CC0 / public domain. No NASA endorsement implied.
"""

RU = """
**Конвейер.** Данные NASA -> проверенные таблицы -> физика -> калибровка + машинное обучение -> валидация -> ранжированные выводы.

1. **Данные.** Репозиторий NASA PSI: все 24 исследования по горению; FLEX (тесты с каплями на МКС) сверен ячейка за ячейкой с
   NASA/TP-2015-216046 (0 расхождений); аномалии помечены флагами и никогда не исправлялись молча.
2. **Физика.** Квазистационарное горение капли с рецептурой свойств Law & Williams (1972): константа скорости горения
   `K = 8 lambda_1 / (rho_F c_1) ln(1 + B)`; теплоёмкость паров топлива, смешанная теплопроводность (0.4 пары топлива +
   0.6 окружающий газ), равновесная температура пламени с учётом диссоциации. Свойства из NIST и отчётов NASA. Гравитация:
   поправка на плавучесть `K (1 + 0.533 Gr^0.52)`, где `Gr` пропорционально g (Земля 1 g, Луна 1/6 g как верхняя граница).
3. **Гибридная модель.** `ln K = ln K_теория + ln c_топливо + поправка гауссовского процесса` только по условиям, известным до
   зажигания; 95 % полоса неопределённости; метки "в пределах данных" / "экстраполяция" / "ненадёжно".
4. **Валидация.** Кросс-валидация с группировкой по режимам испытаний, экстраполяция с исключением целого класса условий,
   проверки физичности, чувствительность к определению метки затухания.
5. **Выводы.** Ранжируются по `S = w_доказательства x ln(1 + n_тестов) x (0.3 + 0.7 e)`; веса доказательств: данные NASA 1.0,
   модель 0.7, литература NASA 0.6, физическая теория 0.5, история NASA 0.5, спинофф NASA 0.3. Исследования ранжируются по
   0.5 x роль для пожарной безопасности + 0.3 x пригодные данные + 0.2 x объём данных.

**Официальные ресурсы челленджа и как они использованы**

| # | Ресурс | Использование |
|---|---|---|
| R1 | NASA Physical Sciences Informatics (psi.nasa.gov) | все количественные данные: 24 исследования, таблицы FLEX, CFI-G, BASS-II, SAME-R |
| R2 | NASA SMA - Apollo 1 | урок: чистый O2 быстро распространяет огонь, убивает CO (связано с выводами про O2 и CO) |
| R3 | NASA SMA - Apollo 13 | урок: кислородные системы + электрический нагрев как источник зажигания |
| R4 | NASA History - пожар на "Мире" 1997 | урок: реальный пожар в невесомости, дым часами, перекрыт путь эвакуации |
| R5-R7 | NASA Spinoff - баллоны, детектор пожара, огнестойкое снаряжение | польза на Земле |

**Другие источники.** Отчёты NASA NTRS (технический отчёт FLEX, Svehla 1962, RP-1311, TM-4513, работы по горючести на Луне),
NIST Chemistry WebBook, Law & Williams (1972, Combustion and Flame), Cantera (равновесие). Полный список с лицензиями:
`docs/DATA_SOURCES.md`.

**Использование ИИ.** Код, анализ и тексты сделаны с помощью Claude Code (Anthropic) под руководством участника команды,
который принимал все научные и проектные решения (`docs/DECISIONS.md`, `docs/AI_USAGE.md`). Изображений, созданных ИИ, нет.

**Ограничения.** Два топлива из одного эксперимента; температура среды на МКС около 298 K; данных при частичной гравитации
в PSI нет; классификатор затухания слаб вне испытанных атмосфер; коэффициент для Земли (1 g) - экстраполированная физическая
оценка.

Репозиторий: https://github.com/ruska51/prometheus-0g - код Apache-2.0; данные NASA CC0 / общественное достояние. Одобрение
NASA не подразумевается.
"""

st.title(t("Method & sources"))
st.markdown(RU if lang() == "ru" else EN)
